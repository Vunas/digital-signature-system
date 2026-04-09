from pydantic import BaseModel, ConfigDict
from datetime import datetime


class DocumentResponse(BaseModel):
    id: int
    file_name: str
    file_size: int
    file_hash: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
