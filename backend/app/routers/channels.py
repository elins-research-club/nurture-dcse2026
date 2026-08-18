from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies.auth import require_admin
from app.models.user import User
from app.schemas.thingspeak_channel import ChannelResponse, ChannelCreate, ChannelUpdate
from app.repositories import channel_repo, node_repo

router = APIRouter(prefix="/nodes")

@router.get("/{node_id}/channel/", response_model=ChannelResponse)
async def get_channel(node_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    channel = await channel_repo.get_by_node_id(db, node.id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel

@router.post("/{node_id}/channel/", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(node_id: str, channel_data: ChannelCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    existing = await channel_repo.get_by_node_id(db, node.id)
    if existing:
        raise HTTPException(status_code=400, detail="Channel config already exists for this node")
    return await channel_repo.create(
        db, 
        node_id=node.id, 
        channel_id=channel_data.channel_id, 
        read_api_key=channel_data.read_api_key, 
        write_api_key=channel_data.write_api_key
    )

@router.put("/{node_id}/channel/", response_model=ChannelResponse)
async def update_channel(node_id: str, channel_data: ChannelUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    channel = await channel_repo.get_by_node_id(db, node.id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return await channel_repo.update(db, channel, **channel_data.model_dump(exclude_unset=True))
