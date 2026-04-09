from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


# Lớp cha chứa các field dùng chung
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)


# Dùng khi User đăng ký
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Mật khẩu dạng plain-text")


# Dùng khi trả data về cho Client (TUYỆT ĐỐI KHÔNG CÓ PASSWORD)
class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    # Giúp Pydantic tự động map dữ liệu từ SQLAlchemy Model
    model_config = ConfigDict(from_attributes=True)
