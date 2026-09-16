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
import time
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
# Kapan pemberitahuan TERAKHIR dikirim, dipakai gerbang kirim-ulang di bawah.
# Pakai time.monotonic() supaya tidak kacau kalau jam sistem digeser.
# {sensor_id (str): detik monotonic}
sensor_last_notified: Dict[str, float] = {}
# {node_id (str): detik monotonic}
node_offline_last_notified: Dict[str, float] = {}

# --- Interval kirim-ulang saat kondisi alarm BERTAHAN (detik) ---
#
# Alarm tetap edge-triggered: transisi normal -> di luar ambang SELALU langsung
# dikirim. Angka di bawah hanya mengatur pengingat berikutnya selama nilainya
# belum kembali normal, supaya operator tidak lupa tapi juga tidak dibanjiri.
# Besarannya mengikuti seberapa cepat tiap besaran realistis berubah dan
# seberapa mendesak penanganannya.
INTERVAL_ULANG_NODE_OFFLINE = 30 * 60
INTERVAL_ULANG_DEFAULT = 60 * 60
INTERVAL_ULANG_PER_TIPE: Dict[str, int] = {
    # Kelistrikan: paling mendesak, baterai bisa habis dalam hitungan jam.
    "batt_volt": 30 * 60,
    "batt_current": 30 * 60,
    # Kondisi tanah: berubah dalam hitungan jam.
    "soil_temp": 60 * 60,
    "soil_moisture": 60 * 60,
    "soil_ec": 60 * 60,
    # Unsur hara & pH: bergerak lambat, pengingat terlalu sering tidak berguna.
    "npk_n": 3 * 60 * 60,
    "npk_p": 3 * 60 * 60,
    "npk_k": 3 * 60 * 60,
    "soil_ph": 3 * 60 * 60,
}


def interval_ulang(sensor_type: Optional[str]) -> int:
    """Interval kirim-ulang untuk satu tipe sensor.

    Tipe di luar tabel (air_temp, air_humidity, box_temp, load_*) memakai
    INTERVAL_ULANG_DEFAULT karena belum ditentukan operator.
    """
    return INTERVAL_ULANG_PER_TIPE.get((sensor_type or "").lower(), INTERVAL_ULANG_DEFAULT)


def reset_state() -> None:
    """Kosongkan state -- dipakai pengujian, bukan alur normal."""
    node_online_state.clear()
    sensor_alert_state.clear()
    sensor_last_notified.clear()
    node_offline_last_notified.clear()


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

        # Kirim kalau: (a) baru masuk kondisi alarm -- ini edge-nya, atau
        # (b) masih alarm dan jeda sejak kiriman terakhir sudah lewat.
        sekarang = time.monotonic()
        jeda = interval_ulang(getattr(s, "type", None))
        terakhir = sensor_last_notified.get(sensor_id_str)
        pengingat = (
            di_luar
            and sedang_alarm
            and terakhir is not None
            and (sekarang - terakhir) >= jeda
        )

        if di_luar and (not sedang_alarm or pengingat):
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
            # Dibedakan supaya di halaman Logs kelihatan mana kejadian baru dan
            # mana pengingat kondisi yang belum tertangani.
            awalan = "masih " if pengingat else ""
            await event_log_repo.create(db, EventLogCreate(
                level="WARNING",
                message=f"{s.name} {awalan}({status_str}): {val} {unit}".strip(),
                node_id=node.id,
            ))
            sensor_alert_state[sensor_id_str] = True
            sensor_last_notified[sensor_id_str] = sekarang

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
            # Dibuang supaya kalau nanti alarm lagi, edge pertamanya langsung
            # dikirim tanpa menunggu sisa jeda dari episode sebelumnya.
            sensor_last_notified.pop(sensor_id_str, None)


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
    # Dibuang supaya episode offline berikutnya langsung berbunyi.
    node_offline_last_notified.pop(node.node_id, None)


async def mark_node_offline(db, node, minutes: int) -> None:
    """Catat node mati.

    Kabar dikirim pada transisi online -> offline, lalu diulang tiap
    INTERVAL_ULANG_NODE_OFFLINE selama node belum kembali. Fungsi ini dipanggil
    watchdog tiap 60 detik, jadi gerbang jeda di bawah yang menentukan kapan
    pengingat benar-benar terkirim.
    """
    sekarang = time.monotonic()
    sudah_offline = not node_online_state.get(node.node_id, True)
    if sudah_offline:
        terakhir = node_offline_last_notified.get(node.node_id)
        if terakhir is not None and (sekarang - terakhir) < INTERVAL_ULANG_NODE_OFFLINE:
            return
    await send_telegram_alert(db, format_node_offline_telegram(
        node_name=node.name, node_id=node.node_id, minutes=minutes,
    ))
    judul, isi = format_node_offline_push(node_name=node.name, minutes=minutes)
    await kirim_push(db, judul, isi, "/dashboard")
    await event_log_repo.create(db, EventLogCreate(
        level="ERROR",
        message=(
            f"Node {node.name} {'masih ' if sudah_offline else ''}"
            f"offline (> {minutes} menit tanpa data)."
        ),
        node_id=node.id,
    ))
    node_online_state[node.node_id] = False
    node_offline_last_notified[node.node_id] = sekarang


def is_node_online(node_id: str) -> Optional[bool]:
    """Status terakhir yang tercatat, atau None kalau node belum pernah terlihat."""
    return node_online_state.get(node_id)
