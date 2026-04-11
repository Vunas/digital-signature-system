from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.security import verify_password, create_access_token
from app.repositories.user_repo import user_repo
from app.schemas.user_schema import UserCreate, UserResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Đăng ký tài khoản mới"""
    user = user_repo.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    return user_repo.create(db, obj_in=user_in)


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Đăng nhập và lấy JWT Token"""
    user = user_repo.get_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tên đăng nhập hoặc mật khẩu",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Tạo Token có giá trị trong 30 phút
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
