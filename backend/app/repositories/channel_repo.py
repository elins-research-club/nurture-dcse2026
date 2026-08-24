from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.thingspeak_channel import ThingspeakChannel

async def get_by_id(db: AsyncSession, channel_id: UUID) -> ThingspeakChannel | None:
    result = await db.execute(select(ThingspeakChannel).where(ThingspeakChannel.id == channel_id))
    return result.scalar_one_or_none()

async def get_by_channel_id(db: AsyncSession, channel_id_str: str) -> ThingspeakChannel | None:
    result = await db.execute(select(ThingspeakChannel).where(ThingspeakChannel.channel_id == channel_id_str))
    return result.scalar_one_or_none()

async def list_all(db: AsyncSession) -> list[ThingspeakChannel]:
    result = await db.execute(select(ThingspeakChannel))
    return list(result.scalars().all())

async def get_by_node_id(db: AsyncSession, node_id: UUID) -> list[ThingspeakChannel]:
    result = await db.execute(select(ThingspeakChannel).where(ThingspeakChannel.node_id == node_id))
    return list(result.scalars().all())

async def create(db: AsyncSession, node_id: UUID, channel_id: str, read_api_key: str, write_api_key: str, label: str | None = None) -> ThingspeakChannel:
    channel = ThingspeakChannel(node_id=node_id, channel_id=channel_id, read_api_key=read_api_key, write_api_key=write_api_key, label=label)
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    return channel

async def update(db: AsyncSession, channel: ThingspeakChannel, **kwargs) -> ThingspeakChannel:
    for key, value in kwargs.items():
        if hasattr(channel, key) and value is not None:
            setattr(channel, key, value)
    await db.commit()
    await db.refresh(channel)
    return channel

async def delete(db: AsyncSession, channel: ThingspeakChannel) -> None:
    await db.delete(channel)
    await db.commit()
