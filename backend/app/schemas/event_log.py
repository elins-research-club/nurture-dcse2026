import uuid
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, field_serializer

class EventLogBase(BaseModel):
    level: str
    message: str
    node_id: Optional[uuid.UUID] = None

class EventLogCreate(EventLogBase):
    pass

class EventLogResponse(EventLogBase):
    id: uuid.UUID
    node_name: Optional[str] = None
    node_code: Optional[str] = None
    created_at: datetime
    
    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime, _info):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    
    class Config:
        from_attributes = True
