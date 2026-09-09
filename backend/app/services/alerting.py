"""Status alarm bersama untuk poller HTTP dan listener MQTT.

Dulu tiap modul menyimpan salinan dict-nya sendiri, dan di mode MQTT itu
menghasilkan bug yang tidak kelihatan: watchdog poller menandai node offline di
dict miliknya, lalu ketika data kembali masuk lewat MQTT handler memeriksa dict
MILIKNYA SENDIRI yang masih True. Akibatnya notifikasi "kembali online" tidak
pernah terkirim, dan flag offline di poller tidak pernah kembali True sehingga
node itu tidak pernah bisa memicu alarm offline untuk kedua kalinya.

Selain state, evaluasi ambang batas juga dipusatkan di sini. Sebelumnya blok
yang sama disalin di dua tempat dan sempat berbeda isinya.
"""

import logging
from typing import Any, Dict, Iterable, Optional

from app.repositories.event_log_repo import event_log_repo
from app.schemas.event_log import EventLogCreate
from app.services.telegram_service import send_telegram_alert
from app.services.webpush_service import kirim_push
from app.services.alert_formatter import (
    format_sensor_alert_telegram,
    format_sensor_recovered_telegram,
    format_sensor_push,
    format_sensor_recovered_push,
    format_node_offline_telegram,
    format_node_online_telegram,
    format_node_offline_push,
    format_node_online_push,
)

logger = logging.getLogger(__name__)

# Satu-satunya salinan. Jangan bikin dict serupa di modul lain.
# {node_id (str): sedang online}
node_online_state: Dict[str, bool] = {}
# {sensor_id (str): sedang di luar ambang}
sensor_alert_state: Dict[str, bool] = {}


def reset_state() -> None:
    """Kosongkan state -- dipakai pengujian, bukan alur normal."""
    node_online_state.clear()
    sensor_alert_state.clear()


async def evaluate_sensor_thresholds(
    db,
    node,
    sensors: Iterable[Any],
    data: Dict[str, Any],
) -> None:
    """Bandingkan pembacaan dengan ambang operator, kirim notifikasi sekali per transisi.

    `data` memakai kunci gabungan "<channel_uuid>_<field>". Field yang hilang
    berarti sensornya gagal dibaca -- dilewati, bukan dianggap nol.
    """
    for s in sensors:
        if not s.enabled:
            continue
        if s.min_threshold is None and s.max_threshold is None:
            continue

        val = data.get(f"{s.channel_id}_{s.thingspeak_field}")
        if val is None or isinstance(val, bool) or not isinstance(val, (int, float)):
            continue

        sensor_id_str = str(s.id)
        sedang_alarm = sensor_alert_state.get(sensor_id_str, False)
        unit = s.unit or ""

        terlalu_tinggi = s.max_threshold is not None and val > s.max_threshold
        terlalu_rendah = s.min_threshold is not None and val < s.min_threshold
        di_luar = terlalu_tinggi or terlalu_rendah

        if di_luar and not sedang_alarm:
            await send_telegram_alert(db, format_sensor_alert_telegram(
                node_name=node.name, sensor_name=s.name, val=val, unit=unit,
                is_high=terlalu_tinggi,
                min_thresh=s.min_threshold, max_thresh=s.max_threshold,
            ))
            judul, isi = format_sensor_push(
                node_name=node.name, sensor_name=s.name, val=val, unit=unit,
                is_high=terlalu_tinggi,
                min_thresh=s.min_threshold, max_thresh=s.max_threshold,
            )
            await kirim_push(db, judul, isi, "/dashboard")

            status_str = "Tinggi" if terlalu_tinggi else "Rendah"
            await event_log_repo.create(db, EventLogCreate(
                level="WARNING",
                message=f"{s.name} ({status_str}): {val} {unit}".strip(),
                node_id=node.id,
            ))
            sensor_alert_state[sensor_id_str] = True

        elif not di_luar and sedang_alarm:
            # Pemulihan ikut diberitahukan. Formatter-nya sudah lama ada tapi
            # tidak pernah dipanggil, jadi operator cuma dapat kabar buruk.
            await send_telegram_alert(db, format_sensor_recovered_telegram(
                node_name=node.name, sensor_name=s.name, val=val, unit=unit,
                min_thresh=s.min_threshold, max_thresh=s.max_threshold,
            ))
            judul, isi = format_sensor_recovered_push(
                node_name=node.name, sensor_name=s.name, val=val, unit=unit,
            )
            await kirim_push(db, judul, isi, "/dashboard")

            await event_log_repo.create(db, EventLogCreate(
                level="INFO",
                message=f"{s.name} kembali normal: {val} {unit}".strip(),
                node_id=node.id,
            ))
            sensor_alert_state[sensor_id_str] = False


async def mark_node_online(db, node) -> None:
    """Catat node hidup. Kirim kabar hanya kalau sebelumnya tercatat offline."""
    sebelumnya = node_online_state.get(node.node_id, True)
    if not sebelumnya:
        await send_telegram_alert(db, format_node_online_telegram(
            node_name=node.name, node_id=node.node_id,
        ))
        judul, isi = format_node_online_push(node_name=node.name)
        await kirim_push(db, judul, isi, "/dashboard")
        await event_log_repo.create(db, EventLogCreate(
            level="INFO",
            message=f"Node {node.name} kembali online.",
            node_id=node.id,
        ))
    node_online_state[node.node_id] = True


async def mark_node_offline(db, node, minutes: int) -> None:
    """Catat node mati. Kirim kabar hanya pada transisi online -> offline."""
    if not node_online_state.get(node.node_id, True):
        return
    await send_telegram_alert(db, format_node_offline_telegram(
        node_name=node.name, node_id=node.node_id, minutes=minutes,
    ))
    judul, isi = format_node_offline_push(node_name=node.name, minutes=minutes)
    await kirim_push(db, judul, isi, "/dashboard")
    await event_log_repo.create(db, EventLogCreate(
        level="ERROR",
        message=f"Node {node.name} offline (> {minutes} menit tanpa data).",
        node_id=node.id,
    ))
    node_online_state[node.node_id] = False


def is_node_online(node_id: str) -> Optional[bool]:
    """Status terakhir yang tercatat, atau None kalau node belum pernah terlihat."""
    return node_online_state.get(node_id)
