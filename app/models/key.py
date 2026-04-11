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


class KeyStorageType(str, enum.Enum):
    server = "server"
    usb_token = "usb_token"
    hsm = "hsm"
    local = "local"


class SignatureAlgo(str, enum.Enum):
    RSA = "RSA"
    ECDSA = "ECDSA"


class Key(Base):
    __tablename__ = "keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)

    key_name = Column(String(100))

    # BYTEA trong Postgres tương đương LargeBinary trong SQLAlchemy
    public_key = Column(LargeBinary, nullable=False)
    private_key_encrypted = Column(LargeBinary, nullable=False)

    key_size = Column(Integer, default=2048)
    algorithm = Column(Enum(SignatureAlgo), default=SignatureAlgo.RSA)

    storage_type = Column(Enum(KeyStorageType), default=KeyStorageType.server)
    storage_provider = Column(String(50))

    key_fingerprint = Column(Text)
    is_revoked = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner = relationship("User", back_populates="keys")
    certificates = relationship(
        "Certificate", back_populates="key", cascade="all, delete"
    )
