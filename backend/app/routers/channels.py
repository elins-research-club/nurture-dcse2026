from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.dependencies.auth import get_optional_current_user, require_admin
from app.models.user import User
from app.schemas.thingspeak_channel import ChannelResponse, ChannelCreate, ChannelUpdate
from app.repositories import channel_repo, node_repo
from app.services.field_decoder import LAYOUT_NODE1_PACKED, is_support_channel

from app.models.sensor import Sensor
from sqlalchemy import delete

# --------------------------------------------------------------------------
# Peta field seed, mengikuti "Channel map" di CLAUDE.md.
#
# Ini cuma nilai awal supaya kanal baru tidak kosong; operator tetap bisa
# mengubahnya lewat UI. Tapi kalau peta di bawah salah, sensor yang terbentuk
# salah label sejak awal dan itu baru ketahuan jauh di belakang.
#
# Kanal utama identik untuk kedua node, KECUALI field6: Node 1 memakainya untuk
# probe analog 1, Node 2 tidak punya probe analog sama sekali.
# --------------------------------------------------------------------------

# Peta field ThingSpeak terverifikasi dari firmware .ino:
# Node 1:
#   Kanal Utama (Ch 1):
#     field1: Nitrogen (npk_n, mg/kg)
#     field2: Fosfor (npk_p, mg/kg)
#     field3: Kalium (npk_k, mg/kg)
#     field4: pH Tanah (soil_ph, pH)
#     field5: EC Tanah (soil_ec, uS/cm)
#     field6: Rata-rata Kelembapan Tanah (soil_moisture, %)
#     field7: Suhu Luar Rata-Rata (air_temp, C)
#     field8: Lembab Luar Rata-Rata (air_humidity, %)
#   Kanal Pendukung (Ch 2):
#     field1: Suhu Tanah (soil_temp, C)
#     field2: Tegangan Baterai (batt_volt, V)
#     field3: Tegangan Load (load_volt, V)
#     field4: Arus Baterai (batt_current, A)
#     field5: Arus Load (load_current, A)
#     field6: Suhu Dalam Panel (box_temp, C)
#     field7: Status Aktuator (actuator, "")
#     field8: Daya Beban Aktual (load_power, W)
#
# Node 2:
#   Kanal Utama (Ch 1):
#     field1: Nitrogen (npk_n, mg/kg)
#     field2: Fosfor (npk_p, mg/kg)
#     field3: Kalium (npk_k, mg/kg)
#     field4: pH Tanah (soil_ph, pH)
#     field5: EC Tanah (soil_ec, uS/cm)
#     field6: Suhu Luar Rata-Rata (air_temp, C)
#     field7: Lembab Luar Rata-Rata (air_humidity, %)
#     field8: Daya Beban Aktual (load_power, W)
#   Kanal Pendukung (Ch 2):
#     field1: Suhu Tanah (soil_temp, C)
#     field2: Kelembapan Probe NPK (soil_moisture, %)
#     field3: Tegangan Baterai (batt_volt, V)
#     field4: Tegangan Load (load_volt, V)
#     field5: Arus Baterai (batt_current, A)
#     field6: Arus Load (load_current, A)
#     field7: Suhu Dalam Panel (box_temp, C)
#     field8: Status Aktuator (actuator, "")

TEMPLATE_UTAMA_NODE1 = [
    {"name": "Nitrogen", "field": "field1", "unit": "mg/kg", "type": "npk_n"},
    {"name": "Fosfor", "field": "field2", "unit": "mg/kg", "type": "npk_p"},
    {"name": "Kalium", "field": "field3", "unit": "mg/kg", "type": "npk_k"},
    {"name": "pH Tanah", "field": "field4", "unit": "pH", "type": "soil_ph"},
    {"name": "EC Tanah", "field": "field5", "unit": "uS/cm", "type": "soil_ec"},
    {"name": "Rata-rata Kelembapan Tanah", "field": "field6", "unit": "%", "type": "soil_moisture"},
    {"name": "Suhu Luar Rata-Rata", "field": "field7", "unit": "C", "type": "air_temp"},
    {"name": "Lembab Luar Rata-Rata", "field": "field8", "unit": "%", "type": "air_humidity"},
]

TEMPLATE_PENDUKUNG_NODE1 = [
    {"name": "Suhu Tanah", "field": "field1", "unit": "C", "type": "soil_temp"},
    {"name": "Tegangan Baterai", "field": "field2", "unit": "V", "type": "batt_volt"},
    {"name": "Tegangan Load", "field": "field3", "unit": "V", "type": "load_volt"},
    {"name": "Arus Baterai", "field": "field4", "unit": "A", "type": "batt_current"},
    {"name": "Arus Load", "field": "field5", "unit": "A", "type": "load_current"},
    {"name": "Suhu Dalam Panel", "field": "field6", "unit": "C", "type": "box_temp"},
    {"name": "Status Aktuator", "field": "field7", "unit": "", "type": "actuator"},
    {"name": "Daya Beban Aktual", "field": "field8", "unit": "W", "type": "load_power"},
]

TEMPLATE_UTAMA_NODE2 = [
    {"name": "Nitrogen", "field": "field1", "unit": "mg/kg", "type": "npk_n"},
    {"name": "Fosfor", "field": "field2", "unit": "mg/kg", "type": "npk_p"},
    {"name": "Kalium", "field": "field3", "unit": "mg/kg", "type": "npk_k"},
    {"name": "pH Tanah", "field": "field4", "unit": "pH", "type": "soil_ph"},
    {"name": "EC Tanah", "field": "field5", "unit": "uS/cm", "type": "soil_ec"},
    {"name": "Suhu Luar Rata-Rata", "field": "field6", "unit": "C", "type": "air_temp"},
    {"name": "Lembab Luar Rata-Rata", "field": "field7", "unit": "%", "type": "air_humidity"},
    {"name": "Daya Beban Aktual", "field": "field8", "unit": "W", "type": "load_power"},
]

TEMPLATE_PENDUKUNG_NODE2 = [
    {"name": "Suhu Tanah", "field": "field1", "unit": "C", "type": "soil_temp"},
    {"name": "Kelembapan Probe NPK", "field": "field2", "unit": "%", "type": "soil_moisture"},
    {"name": "Tegangan Baterai", "field": "field3", "unit": "V", "type": "batt_volt"},
    {"name": "Tegangan Load", "field": "field4", "unit": "V", "type": "load_volt"},
    {"name": "Arus Baterai", "field": "field5", "unit": "A", "type": "batt_current"},
    {"name": "Arus Load", "field": "field6", "unit": "A", "type": "load_current"},
    {"name": "Suhu Dalam Panel", "field": "field7", "unit": "C", "type": "box_temp"},
    {"name": "Status Aktuator", "field": "field8", "unit": "", "type": "actuator"},
]


def pilih_template(layout: str, label: str | None, urutan: int) -> list[dict]:
    """Pilih peta field sesuai node dan peran kanal.

    Peran dibaca dari label kalau ada; kalau operator tidak memberi label,
    kanal pertama dianggap utama dan sisanya pendukung.
    """
    pendukung = is_support_channel(label) if label else urutan > 0
    node1 = layout == LAYOUT_NODE1_PACKED

    if node1:
        return TEMPLATE_PENDUKUNG_NODE1 if pendukung else TEMPLATE_UTAMA_NODE1
    else:
        return TEMPLATE_PENDUKUNG_NODE2 if pendukung else TEMPLATE_UTAMA_NODE2


router = APIRouter(prefix="/nodes")

async def _find_node(db: AsyncSession, node_id: str):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        try:
            node = await node_repo.get_by_id(db, UUID(node_id))
        except (ValueError, TypeError):
            pass
    return node

@router.get("/{node_id}/channels/", response_model=list[ChannelResponse])
async def list_channels(node_id: str, db: AsyncSession = Depends(get_db), current_user: Optional[User] = Depends(get_optional_current_user)):
    node = await _find_node(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return await channel_repo.get_by_node_id(db, node.id)

@router.get("/{node_id}/channels/{channel_id}/", response_model=ChannelResponse)
async def get_channel(node_id: str, channel_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await _find_node(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    channel = await channel_repo.get_by_id(db, channel_id)
    if not channel or channel.node_id != node.id:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel

@router.post("/{node_id}/channels/", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(node_id: str, channel_data: ChannelCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await _find_node(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    existing_channels = await channel_repo.get_by_node_id(db, node.id)
    channel_index = len(existing_channels)

    channel = await channel_repo.create(
        db,
        node_id=node.id,
        channel_id=channel_data.channel_id,
        read_api_key=channel_data.read_api_key,
        write_api_key=channel_data.write_api_key,
        label=channel_data.label or ("Utama" if channel_index == 0 else "Pendukung")
    )

    # Seed sensor sesuai layout node dan peran kanal.
    for s in pilih_template(node.field_layout, channel.label, channel_index):
        db.add(Sensor(
            node_id=node.id,
            channel_id=channel.id,
            type=s["type"],
            name=s["name"],
            unit=s["unit"],
            thingspeak_field=s["field"],
            enabled=True,
        ))
    await db.commit()

    return channel

@router.put("/{node_id}/channels/{channel_id}/", response_model=ChannelResponse)
async def update_channel(node_id: str, channel_id: UUID, channel_data: ChannelUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await _find_node(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    channel = await channel_repo.get_by_id(db, channel_id)
    if not channel or channel.node_id != node.id:
        raise HTTPException(status_code=404, detail="Channel not found")
    return await channel_repo.update(db, channel, **channel_data.model_dump(exclude_unset=True))

@router.delete("/{node_id}/channels/{channel_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(node_id: str, channel_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await _find_node(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    channel = await channel_repo.get_by_id(db, channel_id)
    if not channel or channel.node_id != node.id:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Delete associated sensors first to maintain clean data integrity
    await db.execute(delete(Sensor).where(Sensor.channel_id == channel.id))
    await channel_repo.delete(db, channel)
