from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies.auth import get_current_user, get_optional_current_user, require_admin
from app.models.user import User
from app.schemas.sensor import SensorResponse, SensorCreate, SensorUpdate
from app.repositories import sensor_repo, node_repo, channel_repo

router = APIRouter(prefix="/nodes")

async def _find_node(db: AsyncSession, node_id: str):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        try:
            node = await node_repo.get_by_id(db, UUID(node_id))
        except (ValueError, TypeError):
            pass
    return node

@router.get("/{node_id}/sensors/", response_model=list[SensorResponse])
async def list_sensors(node_id: str, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: Optional[User] = Depends(get_optional_current_user)):
    node = await _find_node(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return await sensor_repo.list_by_node(db, node.id, skip=skip, limit=limit)

@router.post("/{node_id}/sensors/", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
async def create_sensor(node_id: str, sensor_data: SensorCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await _find_node(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
        
    channel = await channel_repo.get_by_id(db, sensor_data.channel_id)
    if not channel or channel.node_id != node.id:
        raise HTTPException(status_code=400, detail="Invalid channel_id or channel does not belong to this node")
        
    return await sensor_repo.create(
        db, 
        node_id=node.id, 
        channel_id=sensor_data.channel_id,
        type=sensor_data.type, 
        name=sensor_data.name, 
        unit=sensor_data.unit, 
        thingspeak_field=sensor_data.thingspeak_field
    )

@router.put("/{node_id}/sensors/{sensor_id}", response_model=SensorResponse)
async def update_sensor(node_id: str, sensor_id: UUID, sensor_data: SensorUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await _find_node(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    sensor = await sensor_repo.get_by_id(db, sensor_id)
    if not sensor or sensor.node_id != node.id:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return await sensor_repo.update(db, sensor, **sensor_data.model_dump(exclude_unset=True))

@router.delete("/{node_id}/sensors/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sensor(node_id: str, sensor_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await _find_node(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    sensor = await sensor_repo.get_by_id(db, sensor_id)
    if not sensor or sensor.node_id != node.id:
        raise HTTPException(status_code=404, detail="Sensor not found")
    await sensor_repo.delete(db, sensor)
