from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class ActuatorBase(BaseModel):
    node_id: UUID
    type: str
    name: str
    current_state: str = "OFF"
    controllable: bool = True
    enabled: bool = True

class ActuatorCreate(ActuatorBase):
    pass

class ActuatorUpdate(BaseModel):
    type: Optional[str] = None
    name: Optional[str] = None
    current_state: Optional[str] = None
    controllable: Optional[bool] = None
    enabled: Optional[bool] = None

class ActuatorResponse(ActuatorBase):
    id: UUID
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
