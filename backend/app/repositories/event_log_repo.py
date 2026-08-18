from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event_log import EventLog
from app.schemas.event_log import EventLogCreate
import uuid

class EventLogRepository:
    async def create(self, db: AsyncSession, obj_in: EventLogCreate) -> EventLog:
        db_obj = EventLog(
            level=obj_in.level,
            message=obj_in.message,
            node_id=obj_in.node_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100, level: Optional[str] = None) -> List[EventLog]:
        query = select(EventLog).order_by(EventLog.created_at.desc())
        if level:
            query = query.filter(EventLog.level == level)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

event_log_repo = EventLogRepository()
