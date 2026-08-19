import httpx
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.config import settings
from app.models.system_config import SystemConfig

logger = logging.getLogger(__name__)

async def send_telegram_alert(db: AsyncSession, message: str) -> bool:
    # Try fetching from DB first
    result = await db.execute(select(SystemConfig).filter_by(id=1))
    config = result.scalars().first()
    
    bot_token = config.telegram_bot_token if config and config.telegram_bot_token else settings.TELEGRAM_BOT_TOKEN
    chat_id = config.telegram_chat_id if config and config.telegram_chat_id else settings.TELEGRAM_CHAT_ID

    if not bot_token or not chat_id:
        logger.warning("Telegram credentials not configured in DB or .env. Skipping alert.")
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            if response.status_code != 200:
                logger.error(f"Failed to send Telegram message: {response.text}")
                return False
            return True
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return False
