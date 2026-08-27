from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.system_config import SystemConfig
from pydantic import BaseModel
from app.dependencies.auth import require_admin
import httpx

router = APIRouter(prefix="/system")

class SystemConfigSchema(BaseModel):
    offline_threshold_mins: int = 15
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

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
    
    config.offline_threshold_mins = data.offline_threshold_mins
    config.telegram_bot_token = data.telegram_bot_token
    config.telegram_chat_id = data.telegram_chat_id
    
    await db.commit()
    await db.refresh(config)
    return config

@router.post("/test-telegram")
async def test_telegram(db: AsyncSession = Depends(get_db), current_user = Depends(require_admin)):
    result = await db.execute(select(SystemConfig).filter_by(id=1))
    config = result.scalars().first()
    if not config or not config.telegram_bot_token or not config.telegram_chat_id:
        raise HTTPException(status_code=400, detail="Telegram configuration is missing. Save the config first.")
    
    url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": config.telegram_chat_id,
        "text": "✅ G-Connect Test Notification\nYour Telegram integration is working perfectly!"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Telegram API Error: {response.text}")
        return {"message": "Test notification sent successfully!"}
