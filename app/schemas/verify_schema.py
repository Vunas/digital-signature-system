from pydantic import BaseModel
from typing import Optional


class VerifyResponse(BaseModel):
    is_valid: bool
    message: str
    signer_info: Optional[dict] = None
    document_hash: Optional[str] = None
