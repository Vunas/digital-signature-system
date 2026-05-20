from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VerifyLog(Base):
    """Lưu vết các lượt Verify (Xác thực) văn bản từ người dùng/hệ thống"""

    __tablename__ = "verify_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL")
    )
    signature_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("signatures.id", ondelete="SET NULL")
    )
    verified_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_integrity_valid: Mapped[Optional[bool]] = mapped_column(Boolean)
    is_cert_valid: Mapped[Optional[bool]] = mapped_column(Boolean)
    is_not_revoked: Mapped[Optional[bool]] = mapped_column(Boolean)

    message: Mapped[Optional[str]] = mapped_column(Text)
    signer_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
