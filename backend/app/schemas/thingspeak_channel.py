from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class ChannelBase(BaseModel):
    node_id: UUID
    channel_id: str

class ChannelCreate(ChannelBase):
    read_api_key: str
    write_api_key: str

class ChannelUpdate(BaseModel):
    channel_id: Optional[str] = None
    read_api_key: Optional[str] = None
    write_api_key: Optional[str] = None

class ChannelResponse(ChannelBase):
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
