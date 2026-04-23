from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
from typing import Optional
import jwt
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiểm tra mật khẩu người dùng nhập vào có khớp với mã băm trong DB không."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Băm mật khẩu người dùng trước khi lưu vào Database."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Tạo JWT Access Token cho phiên đăng nhập"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    # PyJWT encode trả về string luôn
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Giải mã JWT Token và kiểm tra tính hợp lệ"""
    try:
        if token.startswith("Bearer "):
            token = token.replace("Bearer ", "")

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token đã hết hạn")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Token không hợp lệ: {str(e)}")
