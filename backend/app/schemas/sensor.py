from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class SensorBase(BaseModel):
    node_id: UUID
    channel_id: UUID
    type: str
    name: str
    unit: str
    thingspeak_field: str
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None
    enabled: bool = True

class SensorCreate(BaseModel):
    channel_id: UUID
    type: str
    name: str
    unit: str
    thingspeak_field: str
    enabled: bool = True

class SensorUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    thingspeak_field: Optional[str] = None
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None
    enabled: Optional[bool] = None

class SensorResponse(SensorBase):
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
