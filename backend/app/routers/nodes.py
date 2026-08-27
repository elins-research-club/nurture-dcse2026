from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.dependencies.auth import get_current_user, get_optional_current_user, require_admin
from app.models.user import User
from app.schemas.node import NodeResponse, NodeCreate, NodeUpdate
from app.repositories import node_repo

router = APIRouter(prefix="/nodes")

@router.get("/", response_model=list[NodeResponse])
async def list_nodes(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: Optional[User] = Depends(get_optional_current_user)):
    return await node_repo.list_all(db, skip=skip, limit=limit)

@router.post("/", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
async def create_node(node_data: NodeCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await node_repo.get_by_node_id(db, node_data.node_id)
    if node:
        raise HTTPException(status_code=400, detail="Node ID already registered")
    return await node_repo.create(db, node_id=node_data.node_id, name=node_data.name, location=node_data.location)

@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(node_id: str, db: AsyncSession = Depends(get_db), current_user: Optional[User] = Depends(get_optional_current_user)):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node

@router.put("/{node_id}", response_model=NodeResponse)
async def update_node(node_id: str, node_data: NodeUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return await node_repo.update(db, node, **node_data.model_dump(exclude_unset=True))

@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(node_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    await node_repo.delete(db, node)
