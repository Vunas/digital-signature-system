from app.db.base import Base
from app.db.session import engine


def init_db():
    """
    Hàm này tạo tất cả các bảng dựa trên models nếu chúng chưa tồn tại.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully.")
