from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# Đầu vào khi User muốn verify 1 file
class VerifyRequest(BaseModel):
    document_id: int
    signature_id: int
    # Có thể yêu cầu upload file gốc lên lại qua Form Data thay vì JSON


# Kết quả verify trả về
class VerifyResponse(BaseModel):
    is_valid: bool
    message: str
    verified_at: datetime
    document_name: Optional[str] = None
    signer_username: Optional[str] = None
