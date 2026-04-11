from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.certificate import CertType


class CertificateCreate(BaseModel):
    cert_name: str
    key_id: int
    issuer: str
    subject: str
    valid_days: int = 365
    cert_type: Optional[CertType] = CertType.END_USER
    passphrase: Optional[str] = None
    raw_private_key: Optional[str] = None


class CertificateResponse(BaseModel):
    id: int
    cert_name: str
    issuer: str
    subject: str
    valid_from: datetime
    valid_to: datetime

    class Config:
        from_attributes = True
