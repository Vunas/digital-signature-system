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


# =========================
# ENUM
# =========================
class CertType(str, enum.Enum):
    ROOT = "root"
    INTERMEDIATE = "intermediate"
    END_USER = "end_user"


# =========================
# CERTIFICATE MODEL
# =========================
class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)

    # FK system
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    key_id = Column(Integer, ForeignKey("keys.id", ondelete="CASCADE"), index=True)

    # metadata
    cert_name = Column(String(100))
    serial_number = Column(String(100), unique=True, index=True)

    issuer = Column(String(255))
    subject = Column(String(255))

    cert_type = Column(Enum(CertType), default=CertType.END_USER)
    certificate_data = Column(LargeBinary, nullable=False)
    certificate_pem = Column(Text, nullable=True)
    valid_from = Column(DateTime(timezone=True))
    valid_to = Column(DateTime(timezone=True))

    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # =========================
    # RELATIONSHIPS
    # =========================
    owner = relationship("User", back_populates="certificates")
    key = relationship("Key", back_populates="certificates")

    chains = relationship(
        "CertificateChain",
        back_populates="certificate",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


# =========================
# CERTIFICATE CHAIN (PKI)
# =========================
class CertificateChain(Base):
    __tablename__ = "certificate_chains"

    id = Column(Integer, primary_key=True, index=True)

    certificate_id = Column(
        Integer,
        ForeignKey("certificates.id", ondelete="CASCADE"),
        index=True
    )

    # CA certificate (root/intermediate)
    ca_certificate_data = Column(LargeBinary, nullable=False)

    # level in chain
    # 0 = root CA, 1 = intermediate, 2 = leaf
    level = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    certificate = relationship(
        "Certificate",
        back_populates="chains",
        lazy="selectin"
    )
