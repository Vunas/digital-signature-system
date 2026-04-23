from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, JSON, DateTime, Enum
import enum

from app.db.base import Base


class OutboxStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(Integer, primary_key=True, index=True)
    # Loại dữ liệu liên quan (VD: "Certificate", "User", "Document")
    aggregate_type = Column(String(100), nullable=False, index=True)
    # ID của dữ liệu liên quan
    aggregate_id = Column(String(100), nullable=False, index=True)
    # Tên sự kiện (VD: "CERTIFICATE_CREATED", "USER_REGISTERED")
    event_type = Column(String(100), nullable=False)
    
    # Payload chứa thông tin cần thiết để xử lý sự kiện
    payload = Column(JSON, nullable=False)
    
    status = Column(Enum(OutboxStatus), default=OutboxStatus.PENDING, index=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Ghi lại lý do lỗi (nếu có) để dễ dàng debug và retry
    error_message = Column(String, nullable=True)