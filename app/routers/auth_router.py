from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.dependencies import get_db
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.repositories.user_repo import user_repo
from app.schemas.user_schema import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    user = user_repo.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    return user_repo.create(db, obj_in=user_in)


@router.post("/login")
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Đăng nhập và Set HttpOnly Cookie"""
    user = user_repo.get_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tên đăng nhập hoặc mật khẩu",
        )

    # 1. Tạo 2 loại Token
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    # 2. Gắn vào HttpOnly Cookie
    # secure=True nếu chạy HTTPS trên production, samesite="lax" chống CSRF
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )

    return {"message": "Đăng nhập thành công", "username": user.username}


@router.post("/refresh")
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    """Cấp lại Access Token mới dựa vào Refresh Cookie"""
    refresh_cookie = request.cookies.get("refresh_token")
    if not refresh_cookie:
        raise HTTPException(status_code=401, detail="Refresh token không tồn tại")

    try:
        payload = decode_token(refresh_cookie)
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token không hợp lệ")
    except Exception:
        raise HTTPException(
            status_code=401, detail="Refresh token đã hết hạn hoặc không hợp lệ"
        )

    # Kiểm tra user có tồn tại không
    user = user_repo.get_by_username(db, username=username)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=401, detail="Tài khoản bị khóa hoặc không tồn tại"
        )

    # Tạo Access Token mới và ghi đè Cookie cũ
    new_access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_access_token}",
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return {"message": "Token refreshed"}


@router.post("/logout")
def logout(response: Response):
    """Xóa toàn bộ Cookie khi đăng xuất"""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Đăng xuất thành công"}
