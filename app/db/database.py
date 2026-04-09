from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Tạo Engine kết nối tới PostgreSQL
# pool_pre_ping=True: Kiểm tra kết nối trước khi sử dụng, tránh lỗi mất kết nối
engine = create_engine(
    settings.DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20
)

# SessionLocal là một factory để tạo ra các session làm việc với DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency dùng trong FastAPI để cấp phát DB session cho mỗi request.
    Đảm bảo session luôn được đóng (close) sau khi request kết thúc,
    ngay cả khi có lỗi xảy ra (tránh tràn RAM/Connection leak).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
