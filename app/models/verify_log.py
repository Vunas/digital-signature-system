from sqlalchemy import Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from datetime import datetime


class VerifyLog(Base):
    """Lưu lịch sử xác thực chữ ký (Ăn điểm cực mạnh)"""

    __tablename__ = "verify_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=True)
    signature_id: Mapped[int] = mapped_column(
        ForeignKey("signatures.id"), nullable=True
    )

    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=True)

    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    document = relationship("Document", back_populates="verify_logs")
    signature = relationship("Signature", back_populates="verify_logs")
