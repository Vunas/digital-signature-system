from datetime import datetime, timedelta
from jose import jwt
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import verify_password, get_password_hash
from app.core.config import settings
from app.schemas.user_schema import UserCreate


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def register_user(db: Session, user_in: UserCreate) -> User:
    # Kiểm tra user tồn tại chưa
    user_exists = db.query(User).filter(User.username == user_in.username).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Username đã tồn tại")

    # Băm mật khẩu
    hashed_pwd = get_password_hash(user_in.password)
    new_user = User(username=user_in.username, password_hash=hashed_pwd)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
