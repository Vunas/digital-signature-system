from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base


class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    SIGNED = "SIGNED"
    VERIFIED = "VERIFIED"
    INVALID = "INVALID"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)

    file_name = Column(String(255))
    original_file_path = Column(Text)
    signed_file_path = Column(Text)

    file_size = Column(Integer)
    mime_type = Column(String(50), default="application/pdf")

    file_hash = Column(Text, nullable=False)
    signed_file_hash = Column(Text)

    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner = relationship("User", back_populates="documents")
    signatures = relationship(
        "Signature", back_populates="document", cascade="all, delete"
    )
