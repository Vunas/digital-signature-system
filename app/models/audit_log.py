from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import LogLevel, ActionStatus, TargetResourceType


class AuditLog(Base):
    """Log chống chối bỏ, lưu vết mọi hành động của hệ thống kèm Chain Hashing"""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    action: Mapped[str] = mapped_column(String(50), nullable=False)

    target_type: Mapped[Optional[TargetResourceType]] = mapped_column(Enum(TargetResourceType))
    target_id: Mapped[Optional[str]] = mapped_column(String(255))

    level: Mapped[LogLevel] = mapped_column(Enum(LogLevel), default=LogLevel.INFO)
    status: Mapped[ActionStatus] = mapped_column(Enum(ActionStatus), default=ActionStatus.SUCCESS)

    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    log_hash: Mapped[Optional[str]] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
