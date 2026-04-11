from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    id: int
    user_id: int
    file_name: str
    file_size: int
    mime_type: str
    file_hash: str
    signed_file_hash: Optional[str] = None
    status: DocumentStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
