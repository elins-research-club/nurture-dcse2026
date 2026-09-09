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

class TelegramTestRequest(BaseModel):
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

def format_telegram_error(error_desc: str, chat_id: str, bot_username: Optional[str] = None) -> str:
    desc_lower = error_desc.lower()
    is_group = str(chat_id).strip().startswith("-")
    bot_ref = f"@{bot_username}" if bot_username else "bot"

    if "chat not found" in desc_lower:
        if is_group:
            return (
                f"Grup Telegram tidak ditemukan ({chat_id}).\n"
                f"Pastikan bot ({bot_ref}) sudah diundang (invite) ke dalam grup dan Chat ID grup sudah benar (biasanya berawalan -100)."
            )
        else:
            return (
                f"Chat pribadi belum aktif untuk ID: {chat_id}.\n"
                f"Di Telegram, pengguna harus membuka {bot_ref} terlebih dahulu dan menekan tombol 'START'. "
                f"Setelah menekan Start di Telegram, silakan klik kembali tombol Uji Koneksi."
            )
    elif "bot was blocked by the user" in desc_lower:
        return f"{bot_ref} sedang diblokir oleh akun Anda. Silakan buka ruang obrolan bot di Telegram lalu pilih 'Unblock'."
    elif "bot is not a member of the group chat" in desc_lower or "bot was kicked" in desc_lower:
        return f"{bot_ref} belum menjadi anggota grup ({chat_id}). Silakan undang bot ke grup tersebut terlebih dahulu."
    elif "chat_id is empty" in desc_lower or "not enough rights" in desc_lower:
        return f"Izin tidak mencukupi atau Chat ID tidak valid. Pastikan {bot_ref} memiliki hak kirim pesan di ruang obrolan."
    elif "unauthorized" in desc_lower:
        return "Token Bot tidak valid atau sudah kedaluwarsa. Periksa kembali token dari @BotFather."
    else:
        return f"Telegram menolak pengiriman: {error_desc}. Pastikan Chat ID dan izin bot sudah sesuai."

@router.post("/test-telegram")
async def test_telegram(
    data: Optional[TelegramTestRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    bot_token = data.telegram_bot_token.strip() if data and data.telegram_bot_token and data.telegram_bot_token.strip() else None
    chat_id = data.telegram_chat_id.strip() if data and data.telegram_chat_id and data.telegram_chat_id.strip() else None
    
    if not bot_token or not chat_id:
        result = await db.execute(select(SystemConfig).filter_by(id=1))
        config = result.scalars().first()
        if config:
            if not bot_token:
                bot_token = config.telegram_bot_token.strip() if config.telegram_bot_token else None
            if not chat_id:
                chat_id = config.telegram_chat_id.strip() if config.telegram_chat_id else None

    if not bot_token or not chat_id:
        raise HTTPException(
            status_code=400,
            detail="Token Bot dan Chat ID harus diisi terlebih dahulu sebelum melakukan uji coba."
        )

    # Ambil username bot untuk pesan bantuan yang ramah
    bot_username = None
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            me_resp = await client.get(f"https://api.telegram.org/bot{bot_token}/getMe")
            if me_resp.status_code == 200:
                bot_username = me_resp.json().get("result", {}).get("username")
    except Exception:
        pass

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "🌱 *G-Connect Smart Farming*\n\n✅ *Notifikasi Uji Coba Berhasil!*\nIntegrasi Bot Telegram Anda telah terhubung dan siap menerima peringatan anomali lahan.",
        "parse_mode": "Markdown"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                raw_desc = response.text
                try:
                    res_json = response.json()
                    raw_desc = res_json.get("description", response.text)
                except Exception:
                    pass
                friendly_message = format_telegram_error(raw_desc, chat_id, bot_username)
                raise HTTPException(status_code=400, detail=friendly_message)
            return {
                "message": "Pesan uji coba berhasil terkirim ke Telegram!",
                "bot_username": bot_username
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal menghubungi server Telegram: {str(e)}")

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

