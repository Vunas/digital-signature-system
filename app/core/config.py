from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Digital Signature PDF API"
    VERSION: str = "1.0.0"

    db_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/digital_signature_db",
    )
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL: str = db_url

    # JWT Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-jwt-key-change-me")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AES Encryption Key (Dùng để mã hóa Private Key khi lưu xuống DB)
    ENCRYPTION_KEY: str = os.getenv(
        "ENCRYPTION_KEY", "uO12M9L4hN4b6s4mXqK_3jJ_n-pXGvL9QvO2zZqE2y0="
    )
    TSA_URL: str = os.getenv("TSA_URL", "http://timestamp.digicert.com")

    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    class Config:
        env_file = ".env"


settings = Settings()
