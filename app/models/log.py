from sqlalchemy import String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from datetime import datetime


class AuditLog(Base):
    """Ghi nhận mọi hành động của hệ thống (Non-repudiation)"""

    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)

    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # LOGIN, SIGN, VERIFY...
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="logs")
