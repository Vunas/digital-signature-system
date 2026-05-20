from datetime import datetime, UTC
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CertType

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.key import Key


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    key_id: Mapped[int] = mapped_column(ForeignKey("keys.id", ondelete="CASCADE"), index=True)

    cert_name: Mapped[Optional[str]] = mapped_column(String(100))
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)

    issuer: Mapped[Optional[str]] = mapped_column(String(255))
    subject: Mapped[Optional[str]] = mapped_column(String(255))

    cert_type: Mapped[CertType] = mapped_column(Enum(CertType), default=CertType.END_ENTITY)
    purpose: Mapped[str] = mapped_column(String(50), default="document_signing")

    certificate_data: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    certificate_pem: Mapped[Optional[str]] = mapped_column(Text)

    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="certificates")
    key: Mapped["Key"] = relationship(back_populates="certificates")
    chains: Mapped[List["CertificateChain"]] = relationship(
        back_populates="certificate", cascade="all, delete-orphan", lazy="selectin"
    )

    def is_valid_now(self) -> bool:
        """Kiểm tra chứng chỉ còn hiệu lực không (Chưa bị thu hồi và còn hạn)"""
        if self.is_revoked:
            return False
        now = datetime.now(UTC)
        if self.valid_from and self.valid_to:
            return self.valid_from <= now <= self.valid_to
        return True

    def revoke(self) -> None:
        """Thu hồi chứng chỉ"""
        self.is_revoked = True
        self.revoked_at = datetime.now(UTC)


class CertificateChain(Base):
    __tablename__ = "certificate_chains"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    certificate_id: Mapped[int] = mapped_column(
        ForeignKey("certificates.id", ondelete="CASCADE"), index=True
    )
    ca_certificate_data: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    level: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    certificate: Mapped["Certificate"] = relationship(back_populates="chains")
