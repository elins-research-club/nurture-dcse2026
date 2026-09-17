from typing import Optional, Tuple
from datetime import datetime, timezone, timedelta

WIB = timezone(timedelta(hours=7))

def get_wib_now_str() -> str:
    return datetime.now(WIB).strftime('%d %b %Y, %H:%M WIB')

def format_sensor_alert_telegram(
    node_name: str,
    sensor_name: str,
    val: float,
    unit: str,
    is_high: bool,
    min_thresh: Optional[float],
    max_thresh: Optional[float]
) -> str:
    status_str = 'Tinggi' if is_high else 'Rendah'
    waktu_wib = get_wib_now_str()
    u = unit or ''
    min_str = f'{min_thresh} {u}'.strip() if min_thresh is not None else '-'
    max_str = f'{max_thresh} {u}'.strip() if max_thresh is not None else '-'
    
    return (
        f'<b>PERINGATAN AMBANG BATAS SENSOR</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'📍 <b>Node</b>     : {node_name}\n'
        f'🌱 <b>Sensor</b>   : {sensor_name}\n'
        f'📊 <b>Nilai</b>    : <b>{val} {u}</b> ({status_str})\n'
        f'🎯 <b>Ambang Batas</b>:\n'
        f'   • Batas Bawah (Min) : {min_str}\n'
        f'   • Batas Atas (Max)  : {max_str}\n'
        f'⏰ <b>Waktu</b>    : {waktu_wib}\n'
        f'━━━━━━━━━━━━━━━━━━━━━'
    )

def format_sensor_recovered_telegram(
    node_name: str,
    sensor_name: str,
    val: float,
    unit: str,
    min_thresh: Optional[float],
    max_thresh: Optional[float]
) -> str:
    waktu_wib = get_wib_now_str()
    u = unit or ''
    
    if min_thresh is not None and max_thresh is not None:
        rentang_str = f'{min_thresh} - {max_thresh} {u}'.strip()
    elif max_thresh is not None:
        rentang_str = f'Maks. {max_thresh} {u}'.strip()
    elif min_thresh is not None:
        rentang_str = f'Min. {min_thresh} {u}'.strip()
    else:
        rentang_str = '-'
        
    return (
        f'<b>KONDISI SENSOR PULIH NORMAL</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'📍 <b>Node</b>     : {node_name}\n'
        f'🌱 <b>Sensor</b>   : {sensor_name}\n'
        f'📊 <b>Nilai</b>    : <b>{val} {u}</b> (Normal)\n'
        f'🎯 <b>Range Aman</b> : {rentang_str}\n'
        f'⏰ <b>Waktu</b>    : {waktu_wib}\n'
        f'━━━━━━━━━━━━━━━━━━━━━'
    )

def format_sensor_push(
    node_name: str,
    sensor_name: str,
    val: float,
    unit: str,
    is_high: bool,
    min_thresh: Optional[float],
    max_thresh: Optional[float]
) -> Tuple[str, str]:
    status_str = 'Tinggi' if is_high else 'Rendah'
    u = unit or ''
    if min_thresh is not None and max_thresh is not None:
        ambang_str = f'{min_thresh} - {max_thresh} {u}'.strip()
    elif max_thresh is not None:
        ambang_str = f'Maks. {max_thresh} {u}'.strip()
    elif min_thresh is not None:
        ambang_str = f'Min. {min_thresh} {u}'.strip()
    else:
        ambang_str = '-'
        
    judul = f'Peringatan: {node_name}'
    isi = f'⚠️ {sensor_name} mencapai {val} {u} ({status_str} | Ambang batas: {ambang_str})'.strip()
    return judul, isi

def format_sensor_recovered_push(
    node_name: str,
    sensor_name: str,
    val: float,
    unit: str
) -> Tuple[str, str]:
    u = unit or ''
    judul = f'Status Normal: {node_name}'
    isi = f'{sensor_name} dalam keadaan normal di angka {val} {u}'.strip()
    return judul, isi

def format_node_offline_telegram(node_name: str, node_id: str, minutes: int) -> str:
    waktu_wib = get_wib_now_str()
    return (
        f'<b>PERINGATAN: ALAT OFFLINE</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'📍 <b>Node</b>    : {node_name} (<code>{node_id}</code>)\n'
        f'⚠️ <b>Status</b>  : Terputus (Tidak ada data > {minutes} Menit)\n'
        f'⏰ <b>Waktu</b>   : {waktu_wib}\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'ℹ️ <i>Silakan periksa catu daya alat atau koneksi jaringan di lapangan.</i>'
    )

def format_node_online_telegram(node_name: str, node_id: str) -> str:
    waktu_wib = get_wib_now_str()
    return (
        f'<b>ALAT KEMBALI ONLINE</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'📍 <b>Node</b>    : {node_name} (<code>{node_id}</code>)\n'
        f'✅ <b>Status</b>  : Terhubung & Aktif Mengirim Data\n'
        f'⏰ <b>Waktu</b>   : {waktu_wib}\n'
        f'━━━━━━━━━━━━━━━━━━━━━'
    )

def format_node_offline_push(node_name: str, minutes: int) -> Tuple[str, str]:
    judul = f'Alat Offline: {node_name}'
    isi = f'🔴 Alat tidak mengirim data selama lebih dari {minutes} menit. Periksa daya atau koneksi internet.'
    return judul, isi

def format_node_online_push(node_name: str) -> Tuple[str, str]:
    judul = f'Alat Online: {node_name}'
    isi = '🟢 Alat telah terhubung kembali dan aktif mengirim data telemetri.'
    return judul, isi
