from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.signature import HashAlgo, SignatureAlgo


class SignatureCreate(BaseModel):
    document_id: int
    key_id: int
    signer_name: str
    signer_reason: Optional[str] = "Xác nhận tài liệu"
    signer_location: Optional[str] = "Việt Nam"
    visible_signature: bool = True

    # Bổ sung 2 trường để hỗ trợ mã hóa và giải mã Khóa
    passphrase: Optional[str] = None
    raw_private_key: Optional[str] = None


class SignatureResponse(BaseModel):
    id: int
    document_id: int
    user_id: int
    hash_algorithm: HashAlgo
    signature_algorithm: SignatureAlgo
    signer_name: str
    signer_reason: str
    signer_location: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
