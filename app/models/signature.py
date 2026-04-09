from sqlalchemy import String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from datetime import datetime


class Signature(Base):
    __tablename__ = "signatures"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    key_id: Mapped[int] = mapped_column(
        ForeignKey("keys.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    signature: Mapped[str] = mapped_column(Text, nullable=False)  # Chữ ký Base64

    hash_algorithm: Mapped[str] = mapped_column(String(50), default="SHA-256")
    signature_algorithm: Mapped[str] = mapped_column(String(50), default="RSA-PSS")

    signed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    document = relationship("Document", back_populates="signatures")
    key = relationship("Key", back_populates="signatures")
    signer = relationship("User", back_populates="signatures")
    verify_logs = relationship("VerifyLog", back_populates="signature")
