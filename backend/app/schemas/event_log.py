import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class EventLogBase(BaseModel):
    level: str
    message: str
    node_id: Optional[uuid.UUID] = None

class EventLogCreate(EventLogBase):
    pass

class EventLogResponse(EventLogBase):
    id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
