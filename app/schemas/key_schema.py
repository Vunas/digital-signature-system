from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class KeyCreate(BaseModel):
    key_name: str
    key_size: int = 2048
    storage_type: str = Field(..., description="'server' hoặc 'local'")
    passphrase: Optional[str] = None


class KeyResponse(BaseModel):
    id: int
    key_name: Optional[str]
    public_key: str
    storage_type: str
    algorithm: str
    is_revoked: bool
    created_at: datetime
    raw_private_key: Optional[str] = None

    class Config:
        from_attributes = True
