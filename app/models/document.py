from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import DocumentStatus

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.signature import Signature


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255))
    original_file_path: Mapped[Optional[str]] = mapped_column(Text)
    signed_file_path: Mapped[Optional[str]] = mapped_column(Text)
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    mime_type: Mapped[str] = mapped_column(String(50), default="application/pdf")
    file_hash: Mapped[str] = mapped_column(Text, nullable=False)
    signed_file_hash: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.UPLOADED
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="documents")
    signatures: Mapped[List["Signature"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

    def mark_as_signed(self, new_signed_path: str, new_signed_hash: str) -> None:
        """Cập nhật trạng thái khi file được ký thành công"""
        self.status = DocumentStatus.SIGNED
        self.signed_file_path = new_signed_path
        self.signed_file_hash = new_signed_hash

    def mark_as_verified(self, is_valid: bool) -> None:
        """Cập nhật trạng thái sau khi hệ thống verify file PDF"""
        self.status = DocumentStatus.VERIFIED if is_valid else DocumentStatus.INVALID
