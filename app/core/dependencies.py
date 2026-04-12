from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from typing import Generator

from app.db.session import SessionLocal
from app.core.config import settings
from app.models.user import User


def get_db() -> Generator:
    """Dependency cung cấp DB session cho mỗi request"""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Lấy thông tin User hiện tại từ HttpOnly Cookie (Access Token)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin (Token không hợp lệ hoặc đã hết hạn)",
    )

    # 1. Lấy token từ Cookie thay vì Header (OAuth2PasswordBearer)
    token = request.cookies.get("access_token")
    if not token:
        raise credentials_exception

    # 2. Xóa tiền tố "Bearer " nếu có (do lúc login chúng ta set là "Bearer <token>")
    if token.startswith("Bearer "):
        token = token.replace("Bearer ", "")

    # 3. Decode JWT Token
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 4. Kiểm tra user trong DB
    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise credentials_exception

    return user
