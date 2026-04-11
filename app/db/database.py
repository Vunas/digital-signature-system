from app.db.base import Base
from app.db.session import engine


def init_db():
    """
    Hàm này tạo tất cả các bảng dựa trên models nếu chúng chưa tồn tại.
    (Giống với câu lệnh CREATE TABLE trong SQL bạn đưa).
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully.")
