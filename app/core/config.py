from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # ========================
    # APP INFO
    # ========================
    PROJECT_NAME: str = "Digital Signature PDF API"
    VERSION: str = "1.0.0"

    # ========================
    # DATABASE
    # ========================
    DATABASE_URL: str = (
        "postgresql://postgres:password@localhost:5432/digital_signature_db"
    )

    # ========================
    # JWT
    # ========================
    SECRET_KEY: str = "your-super-secret-jwt-key-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ========================
    # ENCRYPTION
    # ========================
    ENCRYPTION_KEY: str = "uO12M9L4hN4b6s4mXqK_3jJ_n-pXGvL9QvO2zZqE2y0="
    TSA_URL: str = "http://timestamp.digicert.com"

    # ========================
    # SUPABASE
    # ========================

    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None

    # ========================
    # Pydantic Config
    # ========================
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
