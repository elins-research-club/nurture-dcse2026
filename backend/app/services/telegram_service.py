import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

async def send_telegram_alert(message: str) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not configured. Skipping alert.")
        return False
        
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
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
