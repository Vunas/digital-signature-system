from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from datetime import datetime


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(
        Text, nullable=True
    )  # Có thể null nếu làm Stateless
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)

    file_hash: Mapped[str] = mapped_column(
        Text, nullable=False, index=True
    )  # Lưu SHA-256

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    owner = relationship("User", back_populates="documents")
    signatures = relationship(
        "Signature", back_populates="document", cascade="all, delete-orphan"
    )
    verify_logs = relationship("VerifyLog", back_populates="document")
