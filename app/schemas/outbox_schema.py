from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, Optional
from datetime import datetime
from app.models.outbox_event import OutboxStatus


class OutboxEventCreate(BaseModel):
    aggregate_type: str
    aggregate_id: str
    event_type: str
    payload: Dict[str, Any]


class OutboxEventResponse(OutboxEventCreate):
    id: int
    status: OutboxStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)