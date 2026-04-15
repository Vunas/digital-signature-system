from datetime import timedelta
from sqlalchemy.orm import Session

from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.repositories.user_repo import user_repo
from app.schemas.user_schema import UserCreate

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class AuthService:
    def register_user(self, db: Session, user_in: UserCreate):
        """Xử lý nghiệp vụ đăng ký tài khoản."""
        user = user_repo.get_by_username(db, username=user_in.username)
        if user:
            raise ValueError("Tên đăng nhập đã tồn tại")

        return user_repo.create(db, obj_in=user_in)

    def authenticate_and_generate_tokens(
        self, db: Session, username: str, password: str
    ):
        """Kiểm tra thông tin đăng nhập và sinh cặp token."""
        user = user_repo.get_by_username(db, username=username)

        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Sai tên đăng nhập hoặc mật khẩu")

        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token = create_refresh_token(
            data={"sub": user.username},
            expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        )

        return user, access_token, refresh_token

    def refresh_access_token(self, db: Session, refresh_token_str: str):
        """Giải mã refresh token cũ, kiểm tra trạng thái và cấp quyền mới."""
        if not refresh_token_str:
            raise ValueError("Refresh token không tồn tại")

        try:
            payload = decode_token(refresh_token_str)
            username = payload.get("sub")
            if not username:
                raise ValueError("Token không hợp lệ")
        except Exception:
            raise ValueError("Refresh token đã hết hạn hoặc không hợp lệ")

        user = user_repo.get_by_username(db, username=username)
        if not user or not user.is_active:
            raise ValueError("Tài khoản bị khóa hoặc không tồn tại")

        new_access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return new_access_token


auth_service = AuthService()
