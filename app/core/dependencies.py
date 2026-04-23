from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt
from typing import AsyncGenerator

from app.db.session import AsyncSessionLocal
from app.core.config import settings
from app.models.user import User  # Giả sử bạn có model này


# ==========================================
# PATTERN: CLEAN DI TRANSACTION
# ==========================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Tự động commit sau khi request xử lý xong mà không có lỗi
            await session.commit()
        except Exception:
            # Tự động rollback nếu có lỗi trong service/router
            await session.rollback()
            raise


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """Lấy thông tin User hiện tại từ HttpOnly Cookie (Access Token)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin (Token không hợp lệ hoặc đã hết hạn)",
    )

    token = request.cookies.get("access_token")
    if not token:
        raise credentials_exception

    if token.startswith("Bearer "):
        token = token.replace("Bearer ", "")

    try:
        # Dùng PyJWT thay cho jose
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    # Chuẩn truy vấn SQLAlchemy 2.0 (Async)
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    return user
