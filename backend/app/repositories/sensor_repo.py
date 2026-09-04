from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sensor import Sensor

async def get_by_id(db: AsyncSession, sensor_id: UUID) -> Sensor | None:
    result = await db.execute(select(Sensor).where(Sensor.id == sensor_id))
    return result.scalar_one_or_none()

async def list_by_node(db: AsyncSession, node_id: UUID, skip: int = 0, limit: int = 100) -> list[Sensor]:
    result = await db.execute(select(Sensor).where(Sensor.node_id == node_id).offset(skip).limit(limit))
    return list(result.scalars().all())

async def create(db: AsyncSession, node_id: UUID, channel_id: UUID, type: str, name: str, unit: str, thingspeak_field: str) -> Sensor:
    sensor = Sensor(node_id=node_id, channel_id=channel_id, type=type, name=name, unit=unit, thingspeak_field=thingspeak_field)
    db.add(sensor)
    await db.commit()
    await db.refresh(sensor)
    return sensor

async def update(db: AsyncSession, sensor: Sensor, **kwargs) -> Sensor:
    for key, value in kwargs.items():
        if hasattr(sensor, key):
            setattr(sensor, key, value)
    await db.commit()
    await db.refresh(sensor)
    return sensor

async def delete(db: AsyncSession, sensor: Sensor) -> None:
    await db.delete(sensor)
    await db.commit()
