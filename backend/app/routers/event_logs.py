from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.event_log import EventLogResponse
from app.repositories.event_log_repo import event_log_repo
from app.dependencies.auth import get_optional_current_user

router = APIRouter()

@router.get("/", response_model=List[EventLogResponse])
async def get_event_logs(
    response: Response,
    skip: int = 0,
    limit: int = 25,
    level: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_current_user)
):
    total = await event_log_repo.count(db, level=level)
    response.headers["X-Total-Count"] = str(total)
    return await event_log_repo.get_multi(db, skip=skip, limit=limit, level=level)
