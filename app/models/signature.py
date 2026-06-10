from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SignatureAlgo, HashAlgo

if TYPE_CHECKING:
     from app.models.document import Document
     from app.models.timestamp import Timestamp

class Signature(Base):
    __tablename__ = "signatures"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    key_id: Mapped[int] = mapped_column(ForeignKey("keys.id", ondelete="CASCADE"))
    certificate_id: Mapped[Optional[int]] = mapped_column(ForeignKey("certificates.id"))
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True)

    signature_value: Mapped[Optional[bytes]] = mapped_column(BYTEA)

    hash_algorithm: Mapped[HashAlgo] = mapped_column(Enum(HashAlgo), default=HashAlgo.SHA_256)
    signature_algorithm: Mapped[SignatureAlgo] = mapped_column(
        Enum(SignatureAlgo), default=SignatureAlgo.RSA
    )

    visible_signature: Mapped[bool] = mapped_column(Boolean, default=True)
    signer_name: Mapped[Optional[str]] = mapped_column(String(100))
    signer_reason: Mapped[Optional[str]] = mapped_column(Text)
    signer_location: Mapped[Optional[str]] = mapped_column(String(100))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship(back_populates="signatures")
    timestamps: Mapped[List["Timestamp"]] = relationship(
        back_populates="signature", cascade="all, delete-orphan"
    )
