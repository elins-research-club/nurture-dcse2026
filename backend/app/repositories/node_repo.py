from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.node import Node

async def get_by_id(db: AsyncSession, node_id: UUID) -> Node | None:
    result = await db.execute(select(Node).where(Node.id == node_id))
    return result.scalar_one_or_none()

async def get_by_node_id(db: AsyncSession, node_id: str) -> Node | None:
    result = await db.execute(select(Node).where(Node.node_id == node_id))
    return result.scalar_one_or_none()

async def list_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Node]:
    result = await db.execute(select(Node).offset(skip).limit(limit))
    return list(result.scalars().all())

async def create(db: AsyncSession, node_id: str, name: str, location: str | None,
                 field_layout: str = "node2_plain") -> Node:
    node = Node(node_id=node_id, name=name, location=location, field_layout=field_layout)
    db.add(node)
    await db.commit()
    await db.refresh(node)
    return node

async def update(db: AsyncSession, node: Node, **kwargs) -> Node:
    # Router sudah menyaring lewat model_dump(exclude_unset=True), jadi kunci yang
    # sampai ke sini memang sengaja dikirim. Menolak nilai None/False di sini
    # membuat is_active=False mustahil disimpan -- node tidak pernah bisa
    # dinonaktifkan lewat API.
    for key, value in kwargs.items():
        if hasattr(node, key):
            setattr(node, key, value)
    await db.commit()
    await db.refresh(node)
    return node

async def delete(db: AsyncSession, node: Node) -> None:
    await db.delete(node)
    await db.commit()

async def update_last_seen(db: AsyncSession, node: Node) -> Node:
    node.last_seen = datetime.utcnow()
    await db.commit()
    await db.refresh(node)
    return node
