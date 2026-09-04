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

class TelegramBotInfoRequest(BaseModel):
    token: Optional[str] = None

@router.post("/telegram-bot-info")
@router.get("/telegram-bot-info")
async def get_telegram_bot_info(
    data: Optional[TelegramBotInfoRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    token = data.token.strip() if data and data.token and data.token.strip() else None
    if not token:
        result = await db.execute(select(SystemConfig).filter_by(id=1))
        config = result.scalars().first()
        if config and config.telegram_bot_token:
            token = config.telegram_bot_token.strip()

    if not token:
        return {"is_valid": False, "detail": "Token bot belum dikonfigurasi"}

    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            res_data = resp.json()
            if resp.status_code == 200 and res_data.get("ok"):
                bot = res_data.get("result", {})
                username = bot.get("username", "")
                return {
                    "is_valid": True,
                    "id": bot.get("id"),
                    "first_name": bot.get("first_name"),
                    "username": username,
                    "can_join_groups": bot.get("can_join_groups", True),
                    "link": f"https://t.me/{username}" if username else None
                }
            else:
                return {
                    "is_valid": False,
                    "detail": res_data.get("description", "Token bot tidak valid atau tidak dikenali Telegram.")
                }
    except Exception as e:
        return {
            "is_valid": False,
            "detail": f"Tidak dapat terhubung ke Telegram API: {str(e)}"
        }

