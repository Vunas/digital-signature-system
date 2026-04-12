from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from .config import settings

# Khởi tạo ngữ cảnh băm mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiểm tra mật khẩu người dùng nhập vào có khớp với mã băm trong DB không."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Băm mật khẩu người dùng trước khi lưu vào Database."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Tạo JWT Access Token cho phiên đăng nhập (thời gian sống ngắn)"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Tạo JWT Refresh Token để cấp lại Access Token khi hết hạn (thời gian sống dài)"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Mặc định refresh token sống 7 ngày nếu không chỉ định
        expire = datetime.utcnow() + timedelta(days=7)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Giải mã JWT Token và kiểm tra tính hợp lệ, trả về payload (dữ liệu bên trong token)"""
    try:
        # Xóa chữ "Bearer " nếu lỡ bị dính vào từ cookie
        if token.startswith("Bearer "):
            token = token.replace("Bearer ", "")

        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        # Ném ra lỗi chung để Router bên ngoài có thể xử lý thành HTTPException 401
        raise ValueError(f"Token không hợp lệ hoặc đã hết hạn: {str(e)}")
