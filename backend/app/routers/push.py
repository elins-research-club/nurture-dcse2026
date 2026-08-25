from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.push_subscription import PushSubscription
from app.services.webpush_service import kirim_push

router = APIRouter(prefix="/push")


class KunciLangganan(BaseModel):
    p256dh: str
    auth: str


class LanggananMasuk(BaseModel):
    endpoint: str
    keys: KunciLangganan


@router.get("/public-key")
async def ambil_public_key():
    """Kunci publik VAPID, dibutuhkan browser untuk mendaftar langganan.

    Tidak diberi autentikasi: kunci ini memang dirancang untuk dipublikasikan,
    dan halaman login pun perlu membacanya.
    """
    if not settings.WEBPUSH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Web Push belum dikonfigurasi (kunci VAPID kosong)",
        )
    return {"public_key": settings.VAPID_PUBLIC_KEY}


@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
async def daftar_langganan(
    data: LanggananMasuk,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Menyimpan langganan dari browser. Aman dipanggil berulang."""
    hasil = await db.execute(
        select(PushSubscription).where(PushSubscription.endpoint == data.endpoint)
    )
    ada = hasil.scalars().first()

    if ada:
        # Browser bisa memutar kuncinya tanpa mengganti endpoint, jadi
        # diperbarui, bukan dilewati.
        ada.p256dh = data.keys.p256dh
        ada.auth = data.keys.auth
        await db.commit()
        return {"status": "diperbarui"}

    db.add(
        PushSubscription(
            endpoint=data.endpoint,
            p256dh=data.keys.p256dh,
            auth=data.keys.auth,
            user_agent=request.headers.get("user-agent", "")[:255] or None,
        )
    )
    await db.commit()
    return {"status": "terdaftar"}


@router.delete("/subscribe", status_code=status.HTTP_204_NO_CONTENT)
async def batalkan_langganan(
    data: LanggananMasuk,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await db.execute(
        delete(PushSubscription)
        .where(PushSubscription.endpoint == data.endpoint)
        .execution_options(synchronize_session=False)
    )
    await db.commit()


@router.post("/test")
async def uji_push(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Kirim satu notifikasi uji ke semua perangkat terdaftar."""
    jumlah = await kirim_push(
        db,
        "G-Connect",
        "Uji koneksi berhasil. Alert sensor akan masuk ke sini.",
        "/dashboard",
    )
    if jumlah == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tidak ada perangkat terdaftar, atau semua pengiriman gagal",
        )
    return {"terkirim": jumlah}
