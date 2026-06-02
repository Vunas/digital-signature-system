from pydantic import BaseModel
from typing import Optional

class SignerInfoSchema(BaseModel):
    subject: str
    issuer: str
    reason: str
    has_tsa: bool
    is_entire_file: bool
    coverage_name: str

class VerifyResponse(BaseModel):
    is_valid: bool
    is_integrity_valid: Optional[bool] = None
    is_cert_valid: Optional[bool] = None
    
    message: str
    signer_info: Optional[SignerInfoSchema] = None
    document_hash: Optional[str] = None