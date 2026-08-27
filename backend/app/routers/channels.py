from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.dependencies.auth import require_admin
from app.models.user import User
from app.schemas.thingspeak_channel import ChannelResponse, ChannelCreate, ChannelUpdate
from app.repositories import channel_repo, node_repo

from app.models.sensor import Sensor
from sqlalchemy import delete

CHANNEL_1_TEMPLATES = [
    {"name": "Nitrogen", "field": "field1", "unit": "mg/kg", "type": "npk"},
    {"name": "Phosphorus", "field": "field2", "unit": "mg/kg", "type": "npk"},
    {"name": "Potassium", "field": "field3", "unit": "mg/kg", "type": "npk"},
    {"name": "pH", "field": "field4", "unit": "pH", "type": "soil"},
    {"name": "eC", "field": "field5", "unit": "µS/cm", "type": "soil"},
    {"name": "Rata-rata Kelembapan Tanah", "field": "field6", "unit": "%", "type": "soil"},
    {"name": "Rata-rata Suhu Luar Box Panel", "field": "field7", "unit": "°C", "type": "environment"},
    {"name": "Lembab luar rata-rata", "field": "field8", "unit": "%", "type": "environment"},
]

CHANNEL_2_TEMPLATES = [
    {"name": "Suhu Tanah", "field": "field1", "unit": "°C", "type": "soil"},
    {"name": "Kelembapan Probe NPK", "field": "field2", "unit": "%", "type": "soil"},
    {"name": "Kode Error Modbus", "field": "field3", "unit": "", "type": "system"},
    {"name": "Soil probe 1", "field": "field4", "unit": "%", "type": "soil"},
    {"name": "Soil probe 2", "field": "field5", "unit": "%", "type": "soil"},
    {"name": "Soil probe 3", "field": "field6", "unit": "%", "type": "soil"},
    {"name": "Suhu Dalam Box Panel", "field": "field7", "unit": "°C", "type": "environment"},
    {"name": "Status aktuator", "field": "field8", "unit": "", "type": "actuator"},
]

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
        label=channel_data.label or f"Channel {channel_index + 1}"
    )

    # Automatically seed the 8 standard sensor mappings for this channel
    template = CHANNEL_1_TEMPLATES if channel_index == 0 else CHANNEL_2_TEMPLATES
    for s in template:
        new_sensor = Sensor(
            node_id=node.id,
            channel_id=channel.id,
            type=s["type"],
            name=s["name"],
            unit=s["unit"],
            thingspeak_field=s["field"],
            enabled=True
        )
        db.add(new_sensor)
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
