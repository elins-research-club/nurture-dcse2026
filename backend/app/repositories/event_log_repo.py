from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.event_log import EventLog
from app.schemas.event_log import EventLogCreate, EventLogResponse
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

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100, level: Optional[str] = None) -> List[EventLogResponse]:
        query = select(EventLog).options(selectinload(EventLog.node)).order_by(EventLog.created_at.desc())
        if level:
            query = query.filter(EventLog.level == level)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        logs = result.scalars().all()
        return [
            EventLogResponse(
                id=log.id,
                level=log.level,
                message=log.message,
                node_id=log.node_id,
                node_name=log.node.name if log.node else None,
                node_code=log.node.node_id if log.node else None,
                created_at=log.created_at
            )
            for log in logs
        ]

    async def count(self, db: AsyncSession, level: Optional[str] = None) -> int:
        query = select(func.count(EventLog.id))
        if level:
            query = query.filter(EventLog.level == level)
        result = await db.execute(query)
        return result.scalar() or 0

event_log_repo = EventLogRepository()
