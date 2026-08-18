from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.actuator import Actuator

async def get_by_id(db: AsyncSession, actuator_id: UUID) -> Actuator | None:
    result = await db.execute(select(Actuator).where(Actuator.id == actuator_id))
    return result.scalar_one_or_none()

async def list_by_node(db: AsyncSession, node_id: UUID) -> list[Actuator]:
    result = await db.execute(select(Actuator).where(Actuator.node_id == node_id))
    return list(result.scalars().all())

async def create(db: AsyncSession, node_id: UUID, type: str, name: str, controllable: bool = True) -> Actuator:
    actuator = Actuator(node_id=node_id, type=type, name=name, controllable=controllable)
    db.add(actuator)
    await db.commit()
    await db.refresh(actuator)
    return actuator

async def update(db: AsyncSession, actuator: Actuator, **kwargs) -> Actuator:
    for key, value in kwargs.items():
        if hasattr(actuator, key) and value is not None:
            setattr(actuator, key, value)
    await db.commit()
    await db.refresh(actuator)
    return actuator

async def delete(db: AsyncSession, actuator: Actuator) -> None:
    await db.delete(actuator)
    await db.commit()
