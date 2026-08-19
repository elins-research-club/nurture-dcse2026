from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.system_config import SystemConfig
from pydantic import BaseModel
from app.dependencies.auth import require_admin

router = APIRouter(prefix="/system")

class SystemConfigSchema(BaseModel):
    polling_interval: int
    data_retention_days: int
    offline_threshold_mins: int

@router.get("/config", response_model=SystemConfigSchema)
async def get_config(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemConfig).filter_by(id=1))
    config = result.scalars().first()
    if not config:
        config = SystemConfig(id=1)
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return config

@router.put("/config", response_model=SystemConfigSchema)
async def update_config(data: SystemConfigSchema, db: AsyncSession = Depends(get_db), current_user = Depends(require_admin)):
    result = await db.execute(select(SystemConfig).filter_by(id=1))
    config = result.scalars().first()
    if not config:
        config = SystemConfig(id=1)
        db.add(config)
    
    config.polling_interval = data.polling_interval
    config.data_retention_days = data.data_retention_days
    config.offline_threshold_mins = data.offline_threshold_mins
    
    await db.commit()
    await db.refresh(config)
    return config
