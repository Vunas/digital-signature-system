from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import KeyStorageType, SignatureAlgo

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.certificate import Certificate


class Key(Base):
    __tablename__ = "keys"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    key_name: Mapped[Optional[str]] = mapped_column(String(100))
    public_key: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    private_key_encrypted: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    key_size: Mapped[int] = mapped_column(default=2048)
    algorithm: Mapped[SignatureAlgo] = mapped_column(Enum(SignatureAlgo), default=SignatureAlgo.RSA)
    storage_type: Mapped[KeyStorageType] = mapped_column(
        Enum(KeyStorageType), default=KeyStorageType.SERVER
    )
    storage_provider: Mapped[Optional[str]] = mapped_column(String(50))
    key_fingerprint: Mapped[Optional[str]] = mapped_column(Text)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="keys")
    certificates: Mapped[List["Certificate"]] = relationship(
        back_populates="key", cascade="all, delete-orphan"
    )

    def revoke_key(self) -> None:
        """Đánh dấu khóa đã bị thu hồi/xóa bỏ, không cho phép ký văn bản mới"""
        self.is_revoked = True
