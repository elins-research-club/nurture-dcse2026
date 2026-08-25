import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class PushSubscription(Base):
    """Satu baris per perangkat yang mengizinkan notifikasi.

    Browser yang mendaftar mengembalikan tiga hal: `endpoint` (alamat unik di
    server push Google), serta `p256dh` dan `auth` yang dipakai mengenkripsi
    isi notifikasi. Ketiganya harus disimpan apa adanya -- server push menolak
    permintaan kalau salah satunya tidak cocok.

    Tidak dikaitkan ke user maupun node: siapa pun yang menekan "Izinkan" di
    dashboard menerima seluruh alert. Kalau nanti perlu dipisah per kebun,
    tambahkan kolom node_id di sini.
    """

    __tablename__ = "push_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Panjangnya bisa ratusan karakter dan berbeda tiap browser, jadi Text.
    # Unique supaya perangkat yang mendaftar ulang tidak menumpuk baris.
    endpoint = Column(Text, nullable=False, unique=True)
    p256dh = Column(String(255), nullable=False)
    auth = Column(String(255), nullable=False)

    # Sekadar untuk menelusuri perangkat mana yang bermasalah saat push gagal.
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
