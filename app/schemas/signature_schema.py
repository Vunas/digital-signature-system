from pydantic import BaseModel
from typing import Optional


class SignatureCreate(BaseModel):
    document_id: int
    key_id: int
    passphrase: Optional[str] = None
    private_key: Optional[str] = (
        None  # Dành cho trường hợp người dùng upload file Local .pem
    )


class SignatureResponse(BaseModel):
    id: int
    document_id: int
    key_id: int
    signature: str
    hash_algorithm: str
    signature_algorithm: str

    class Config:
        from_attributes = True
