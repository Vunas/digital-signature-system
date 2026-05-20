from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.services.auth_service import (
    auth_service,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.schemas.user_schema import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Đăng ký tài khoản mới"""
    try:
        user = await auth_service.register_user(db, user_in=user_in)
        await db.commit()  # Unit of Work: Chốt lưu User và AuditLog
        return user
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Đăng nhập và Set HttpOnly Cookie"""
    try:
        user, access_token, refresh_token = await auth_service.authenticate_and_generate_tokens(
            db=db, username=form_data.username, password=form_data.password
        )
        await db.commit()  # Chốt lưu Audit Log
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

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
async def refresh_token(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    """Cấp lại Access Token mới dựa vào Refresh Cookie"""
    refresh_cookie = request.cookies.get("refresh_token")

    if not refresh_cookie:
        raise HTTPException(status_code=401, detail="Refresh token không tồn tại")

    try:
        new_access_token = await auth_service.refresh_access_token(
            db, refresh_token_str=refresh_cookie
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

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
async def logout(response: Response):
    """Xóa toàn bộ Cookie khi đăng xuất"""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Đăng xuất thành công"}
