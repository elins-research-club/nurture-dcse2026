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

    # Firmware menghilangkan field saat pembacaan gagal, dan backend mengisi
    # kekosongan itu dengan nilai valid terakhir supaya kartu tidak berkedip.
    # Dua kolom ini yang membuat pengisian tadi kelihatan: tanpanya, angka basi
    # tidak bisa dibedakan dari pembacaan baru.
    is_stale: bool = False
    reading_at: Optional[str] = None

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

    # Status aktuator hasil decode backend (bitmask field8). Ikut di sini supaya
    # kartu langsung tampil saat halaman dibuka, tanpa menunggu pesan WebSocket.
    aktuator: Optional[Dict[str, bool]] = None

    # Tegangan/arus masuk-keluar plus daya turunan (V x A). Tidak ada field
    # ThingSpeak untuk daya, jadi ia dihitung dan tidak pernah disimpan.
    power_metrics: Dict[str, Any] = {}

    # Vonis dari services/soil_health.py. Bentuknya sengaja dibiarkan bebas
    # supaya sitasi dan catatan kalibrasi ikut terbawa apa adanya ke frontend --
    # kalau dipipihkan jadi satu angka, justru itu yang hilang duluan.
    soil_health: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
