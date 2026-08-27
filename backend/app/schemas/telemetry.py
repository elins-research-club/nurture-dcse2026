from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional, List, Dict, Any

class SensorMetricSummary(BaseModel):
    id: UUID
    name: str
    type: str
    unit: str
    thingspeak_field: str
    channel_id: Optional[UUID] = None
    field_key: str
    current_value: Optional[float] = None
    min_recorded: Optional[float] = None
    max_recorded: Optional[float] = None
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None
    status: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class DashboardSummaryResponse(BaseModel):
    node_id: str
    node_name: Optional[str] = None
    last_seen: Optional[str] = None
    is_active: bool = False
    sensors: List[SensorMetricSummary] = []
    
    # Categorized helpers for structured portlet access
    soil_probes: List[SensorMetricSummary] = []
    npk_sensors: List[SensorMetricSummary] = []
    soil_metrics: Dict[str, Optional[SensorMetricSummary]] = {}
    iot_metrics: Dict[str, Optional[SensorMetricSummary]] = {}
    
    model_config = ConfigDict(from_attributes=True)
