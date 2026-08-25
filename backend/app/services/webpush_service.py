"""Pengiriman Web Push ke perangkat yang sudah mendaftar.

Berbeda dari Telegram yang punya satu tujuan, di sini setiap perangkat punya
langganannya sendiri. Notifikasi dikirim satu per satu, dan langganan yang
sudah mati dibuang saat itu juga.
"""

import asyncio
import json
import logging

from pywebpush import WebPushException, webpush
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)

# Server push membalas kode ini kalau langganannya sudah tidak berlaku --
# aplikasi dihapus, izin dicabut, atau browser membersihkan datanya.
KODE_LANGGANAN_MATI = (404, 410)


def _kirim_satu(langganan: dict, muatan: str) -> None:
    """Panggilan pywebpush yang bersifat blocking. Dijalankan di thread."""
    webpush(
        subscription_info=langganan,
        data=muatan,
        vapid_private_key=settings.VAPID_PRIVATE_KEY,
        vapid_claims={"sub": settings.VAPID_SUBJECT},
    )


async def kirim_push(db: AsyncSession, judul: str, isi: str, url: str = "/dashboard") -> int:
    """Menyiarkan satu notifikasi ke semua perangkat. Mengembalikan jumlah yang berhasil."""
    if not settings.WEBPUSH_ENABLED:
        logger.warning("Kunci VAPID kosong -- Web Push dilewati.")
        return 0

    hasil = await db.execute(select(PushSubscription))
    daftar = list(hasil.scalars().all())
    if not daftar:
        return 0

    muatan = json.dumps({"judul": judul, "isi": isi, "url": url})
    berhasil = 0
    mati: list[str] = []

    for s in daftar:
        langganan = {
            "endpoint": s.endpoint,
            "keys": {"p256dh": s.p256dh, "auth": s.auth},
        }
        try:
            # pywebpush sinkron dan menembak HTTP di dalamnya. Tanpa to_thread,
            # satu perangkat yang lambat akan membekukan seluruh event loop.
            await asyncio.to_thread(_kirim_satu, langganan, muatan)
            berhasil += 1
        except WebPushException as e:
            kode = getattr(e.response, "status_code", None)
            if kode in KODE_LANGGANAN_MATI:
                mati.append(s.endpoint)
            else:
                logger.warning("Web Push gagal (%s): %s", kode, e)
        except Exception as e:
            logger.error("Web Push error tak terduga: %s", e)

    if mati:
        # Dibuang supaya tidak dicoba terus tiap alert berikutnya.
        await db.execute(
            delete(PushSubscription)
            .where(PushSubscription.endpoint.in_(mati))
            .execution_options(synchronize_session=False)
        )
        await db.commit()
        logger.info("%d langganan push mati dibuang.", len(mati))

    return berhasil
