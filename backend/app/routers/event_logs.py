from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.event_log import EventLogResponse
from app.repositories.event_log_repo import event_log_repo
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[EventLogResponse])
async def get_event_logs(
    skip: int = 0,
    limit: int = 100,
    level: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return await event_log_repo.get_multi(db, skip=skip, limit=limit, level=level)
