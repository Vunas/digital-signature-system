from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    LargeBinary,
    Text,
    Enum,
    Boolean,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base


class Timestamp(Base):
    __tablename__ = "timestamps"

    id = Column(Integer, primary_key=True, index=True)
    signature_id = Column(Integer, ForeignKey("signatures.id", ondelete="CASCADE"))

    timestamp_token = Column(LargeBinary)
    hashed_data = Column(Text)
    tsa_name = Column(String(100))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    signature = relationship("Signature", back_populates="timestamps")


class VerifyLog(Base):
    __tablename__ = "verify_logs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    signature_id = Column(Integer, ForeignKey("signatures.id"))

    is_valid = Column(Boolean)
    message = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LogLevel(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    action = Column(String(50))
    level = Column(Enum(LogLevel), default=LogLevel.INFO)
    ip_address = Column(String(50))
    description = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
