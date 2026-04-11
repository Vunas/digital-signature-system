from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Digital Signature PDF API"
    VERSION: str = "1.0.0"

    # Database Configuration (Sửa lại theo DB của bạn)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/digital_signature_db",
    )

    # JWT Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-jwt-key-change-me")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AES Encryption Key (Dùng để mã hóa Private Key khi lưu xuống DB)
    # Phải là base64url-encoded 32-byte key (tạo bằng: cryptography.fernet.Fernet.generate_key())
    ENCRYPTION_KEY: str = os.getenv(
        "ENCRYPTION_KEY", "uO12M9L4hN4b6s4mXqK_3jJ_n-pXGvL9QvO2zZqE2y0="
    )
    TSA_URL: str = os.getenv("TSA_URL", "http://timestamp.digicert.com")

    class Config:
        env_file = ".env"


settings = Settings()
