from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Enum,
    Boolean,
    JSON,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base


# ============================
# ENUMS
# ============================


class LogLevel(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ActionStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"


class TargetResourceType(str, enum.Enum):
    USER = "USER"
    KEY = "KEY"
    CERTIFICATE = "CERTIFICATE"
    DOCUMENT = "DOCUMENT"
    SIGNATURE = "SIGNATURE"
    SYSTEM = "SYSTEM"


# ============================
# TABLES
# ============================


class Timestamp(Base):
    __tablename__ = "timestamps"

    id = Column(Integer, primary_key=True, index=True)
    signature_id = Column(Integer, ForeignKey("signatures.id", ondelete="CASCADE"))

    timestamp_token = Column(Text)  # hoặc LargeBinary nếu cần lưu raw token
    hashed_data = Column(Text)
    tsa_name = Column(String(100))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    signature = relationship("Signature", back_populates="timestamps")


class VerifyLog(Base):
    __tablename__ = "verify_logs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"))
    signature_id = Column(Integer, ForeignKey("signatures.id", ondelete="SET NULL"))
    verified_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    is_valid = Column(Boolean, nullable=False)
    is_integrity_valid = Column(Boolean)
    is_cert_valid = Column(Boolean)
    is_not_revoked = Column(Boolean)

    message = Column(Text)
    signer_snapshot = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    action = Column(String(50), nullable=False)
    target_type = Column(Enum(TargetResourceType))
    target_id = Column(String(255))

    level = Column(Enum(LogLevel), default=LogLevel.INFO)
    status = Column(Enum(ActionStatus), default=ActionStatus.SUCCESS)

    ip_address = Column(String(50))
    user_agent = Column(Text)

    payload = Column(JSON)
    log_hash = Column(String(255))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
