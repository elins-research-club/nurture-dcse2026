from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.dependencies.auth import require_admin
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

TEMPLATE_UTAMA = [
    {"name": "Nitrogen", "field": "field1", "unit": "mg/kg", "type": "npk_n"},
    {"name": "Fosfor", "field": "field2", "unit": "mg/kg", "type": "npk_p"},
    {"name": "Kalium", "field": "field3", "unit": "mg/kg", "type": "npk_k"},
    {"name": "pH Tanah", "field": "field4", "unit": "pH", "type": "soil_ph"},
    {"name": "EC Tanah", "field": "field5", "unit": "uS/cm", "type": "soil_ec"},
    # field6 hanya untuk Node 1 -- disisipkan di bawah.
    {"name": "Suhu Luar Rata-Rata", "field": "field7", "unit": "C", "type": "air_temp"},
    {"name": "Lembab Luar Rata-Rata", "field": "field8", "unit": "%", "type": "air_humidity"},
]

PROBE_ANALOG_1 = {
    "name": "Soil Probe 1", "field": "field6", "unit": "%", "type": "soil_probe",
}

# Kanal pendukung berbeda mulai field3. Node 1 kehabisan field sehingga arus
# masuk dan keluar dipampatkan jadi satu angka di field5; ingest membongkarnya
# jadi field5_in / field5_out (lihat services/field_decoder.py), jadi sensor di
# sini memakai nama field hasil bongkaran itu, bukan "field5" mentah.
TEMPLATE_PENDUKUNG_NODE1 = [
    {"name": "Suhu Tanah", "field": "field1", "unit": "C", "type": "soil_temp"},
    {"name": "Kelembapan Probe NPK", "field": "field2", "unit": "%", "type": "probe_moist"},
    {"name": "Tegangan Input", "field": "field3", "unit": "V", "type": "batt_volt"},
    {"name": "Tegangan Output", "field": "field4", "unit": "V", "type": "batt_volt"},
    {"name": "Arus Input", "field": "field5_in", "unit": "A", "type": "current"},
    {"name": "Arus Output", "field": "field5_out", "unit": "A", "type": "current"},
    {"name": "Soil Probe 2", "field": "field6", "unit": "%", "type": "soil_probe"},
    {"name": "Suhu Dalam Panel", "field": "field7", "unit": "C", "type": "box_temp"},
    # Bitmask, bukan pengukuran. Jangan diberi ambang batas -- angkanya tidak
    # punya urutan yang berarti (12 bukan "lebih besar" dari 3).
    {"name": "Status Aktuator", "field": "field8", "unit": "", "type": "actuator"},
]

TEMPLATE_PENDUKUNG_NODE2 = [
    {"name": "Suhu Tanah", "field": "field1", "unit": "C", "type": "soil_temp"},
    {"name": "Kelembapan Probe NPK", "field": "field2", "unit": "%", "type": "probe_moist"},
    {"name": "Tegangan Input", "field": "field3", "unit": "V", "type": "batt_volt"},
    {"name": "Tegangan Output", "field": "field4", "unit": "V", "type": "batt_volt"},
    {"name": "Arus Input", "field": "field5", "unit": "A", "type": "current"},
    {"name": "Arus Output", "field": "field6", "unit": "A", "type": "current"},
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

    if pendukung:
        return TEMPLATE_PENDUKUNG_NODE1 if node1 else TEMPLATE_PENDUKUNG_NODE2

    utama = list(TEMPLATE_UTAMA)
    if node1:
        # Node 2 tidak punya probe analog, field6-nya kosong.
        utama.insert(5, PROBE_ANALOG_1)
    return utama


router = APIRouter(prefix="/nodes")

@router.get("/{node_id}/channels/", response_model=list[ChannelResponse])
async def list_channels(node_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return await channel_repo.get_by_node_id(db, node.id)

@router.get("/{node_id}/channels/{channel_id}/", response_model=ChannelResponse)
async def get_channel(node_id: str, channel_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    channel = await channel_repo.get_by_id(db, channel_id)
    if not channel or channel.node_id != node.id:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel

@router.post("/{node_id}/channels/", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(node_id: str, channel_data: ChannelCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await node_repo.get_by_node_id(db, node_id)
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
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    channel = await channel_repo.get_by_id(db, channel_id)
    if not channel or channel.node_id != node.id:
        raise HTTPException(status_code=404, detail="Channel not found")
    return await channel_repo.update(db, channel, **channel_data.model_dump(exclude_unset=True))

@router.delete("/{node_id}/channels/{channel_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(node_id: str, channel_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    channel = await channel_repo.get_by_id(db, channel_id)
    if not channel or channel.node_id != node.id:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Delete associated sensors first to maintain clean data integrity
    await db.execute(delete(Sensor).where(Sensor.channel_id == channel.id))
    await channel_repo.delete(db, channel)
