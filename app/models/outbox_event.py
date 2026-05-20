from datetime import datetime, UTC
from typing import Optional, Dict, Any
from sqlalchemy import String, DateTime, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import OutboxStatus


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    aggregate_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[OutboxStatus] = mapped_column(
        Enum(OutboxStatus), default=OutboxStatus.PENDING, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[Optional[str]] = mapped_column(String)

    def mark_processed(self) -> None:
        """Đánh dấu event đã được Worker xử lý thành công"""
        self.status = OutboxStatus.PROCESSED
        self.processed_at = datetime.now(UTC)
        self.error_message = None

    def mark_failed(self, error: str) -> None:
        """Đánh dấu event bị lỗi để Retry sau"""
        self.status = OutboxStatus.FAILED
        self.error_message = str(error)
