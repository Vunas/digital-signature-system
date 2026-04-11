from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    LargeBinary,
    Enum,
    Text,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base
from .key import SignatureAlgo


class HashAlgo(str, enum.Enum):
    SHA_256 = "SHA-256"
    SHA_512 = "SHA-512"


class Signature(Base):
    __tablename__ = "signatures"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    key_id = Column(Integer, ForeignKey("keys.id", ondelete="CASCADE"))
    certificate_id = Column(Integer, ForeignKey("certificates.id"))
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

    signature_value = Column(LargeBinary)

    hash_algorithm = Column(Enum(HashAlgo), default=HashAlgo.SHA_256)
    signature_algorithm = Column(Enum(SignatureAlgo), default=SignatureAlgo.RSA)

    visible_signature = Column(Boolean, default=True)
    signer_name = Column(String(100))
    signer_reason = Column(Text)
    signer_location = Column(String(100))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="signatures")
    timestamps = relationship(
        "Timestamp", back_populates="signature", cascade="all, delete"
    )
