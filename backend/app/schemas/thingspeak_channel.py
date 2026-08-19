from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class ChannelBase(BaseModel):
    channel_id: str
    label: Optional[str] = None

class ChannelCreate(ChannelBase):
    read_api_key: str
    write_api_key: str

class ChannelUpdate(BaseModel):
    channel_id: Optional[str] = None
    read_api_key: Optional[str] = None
    write_api_key: Optional[str] = None
    label: Optional[str] = None

class ChannelResponse(ChannelBase):
    id: UUID
    node_id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
