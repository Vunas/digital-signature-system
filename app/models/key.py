from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from datetime import datetime


class Key(Base):
    __tablename__ = "keys"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    key_name: Mapped[str] = mapped_column(String(100), nullable=True)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    private_key_encrypted: Mapped[str] = mapped_column(Text, nullable=True)
    storage_type: Mapped[str] = mapped_column(String(20), default="server")
    key_size: Mapped[int] = mapped_column(Integer, default=2048)
    algorithm: Mapped[str] = mapped_column(String(50), default="RSA")
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Relationships
    owner = relationship("User", back_populates="keys")
    signatures = relationship("Signature", back_populates="key")
