from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Tách config giúp hệ thống linh hoạt và bảo mật.
    Mọi cấu hình nhạy cảm sẽ được đọc từ file .env hoặc biến môi trường,
    không bao giờ hard-code trực tiếp vào source code.
    """

    PROJECT_NAME: str = "Digital Signature Web App"
    VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str

    # JWT & Security
    SECRET_KEY: str  # Dùng để ký JWT Token
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Salt dùng để tăng cường độ khó khi mã hóa Private Key (KDF)
    # Trong thực tế, nên tạo một chuỗi ngẫu nhiên lưu trong .env
    ENCRYPTION_SALT: str = "super_secret_salt_for_digital_signature_2026"
    SERVER_MASTER_KEY: str = "server-super-secret-master-token-change-in-production"

    # Chỉ định file env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache()
def get_settings() -> Settings:
    """
    Sử dụng lru_cache để cache lại cấu hình, tránh việc đọc file .env
    nhiều lần mỗi khi có request, giúp tăng hiệu năng cực hạn.
    """
    return Settings()


settings = get_settings()
