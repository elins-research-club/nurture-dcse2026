from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.thingspeak_channel import ThingspeakChannel

async def get_by_node_id(db: AsyncSession, node_id: UUID) -> ThingspeakChannel | None:
    result = await db.execute(select(ThingspeakChannel).where(ThingspeakChannel.node_id == node_id))
    return result.scalar_one_or_none()

async def create(db: AsyncSession, node_id: UUID, channel_id: str, read_api_key: str, write_api_key: str) -> ThingspeakChannel:
    channel = ThingspeakChannel(node_id=node_id, channel_id=channel_id, read_api_key=read_api_key, write_api_key=write_api_key)
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
