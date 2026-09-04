from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Literal, Optional

# Harus sama dengan VALID_LAYOUTS di app/services/field_decoder.py.
# "node1_packed" = dua arus dipampatkan di field5 kanal pendukung, ada valve.
# "node2_plain"  = arus float biasa di field5/field6, tidak ada valve.
FieldLayout = Literal["node1_packed", "node2_plain"]


class NodeBase(BaseModel):
    name: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool = True
    field_layout: FieldLayout = "node2_plain"

class NodeCreate(NodeBase):
    node_id: str

class NodeUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None
    field_layout: Optional[FieldLayout] = None

class NodeResponse(NodeBase):
    id: UUID
    node_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
