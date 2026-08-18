from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.actuator import ActuatorResponse, ActuatorCreate, ActuatorUpdate
from app.repositories import actuator_repo, node_repo

router = APIRouter(prefix="/nodes")

@router.get("/{node_id}/actuators/", response_model=list[ActuatorResponse])
async def list_actuators(node_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return await actuator_repo.list_by_node(db, node.id)

@router.post("/{node_id}/actuators/", response_model=ActuatorResponse, status_code=status.HTTP_201_CREATED)
async def create_actuator(node_id: str, actuator_data: ActuatorCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return await actuator_repo.create(
        db, 
        node_id=node.id, 
        type=actuator_data.type, 
        name=actuator_data.name, 
        controllable=actuator_data.controllable
    )

@router.put("/{node_id}/actuators/{actuator_id}", response_model=ActuatorResponse)
async def update_actuator(node_id: str, actuator_id: UUID, actuator_data: ActuatorUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    actuator = await actuator_repo.get_by_id(db, actuator_id)
    if not actuator or actuator.node_id != node.id:
        raise HTTPException(status_code=404, detail="Actuator not found")
    return await actuator_repo.update(db, actuator, **actuator_data.model_dump(exclude_unset=True))

@router.delete("/{node_id}/actuators/{actuator_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_actuator(node_id: str, actuator_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    actuator = await actuator_repo.get_by_id(db, actuator_id)
    if not actuator or actuator.node_id != node.id:
        raise HTTPException(status_code=404, detail="Actuator not found")
    await actuator_repo.delete(db, actuator)
