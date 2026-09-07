"""Bongkar field ThingSpeak yang tidak berisi satu nilai per field.

Node 1 kehabisan slot: arus masuk dan arus keluar dipampatkan jadi satu angka
di field5 kanal pendukung. Node 2 tidak -- arusnya float biasa di field5 dan
field6. Karena itu modul ini bercabang per node, bukan menerapkan satu aturan
ke dua-duanya (lihat CLAUDE.md, "Node 1 field5 encoding").

Layout dibaca dari kolom `nodes.field_layout`, bukan ditebak dari channel_id,
supaya penambahan node ketiga tidak perlu menyentuh kode ini.
"""

from typing import Any, Dict, Optional, Tuple

LAYOUT_NODE1_PACKED = "node1_packed"
LAYOUT_NODE2_PLAIN = "node2_plain"
LAYOUT_DEFAULT = LAYOUT_NODE2_PLAIN
VALID_LAYOUTS = (LAYOUT_NODE1_PACKED, LAYOUT_NODE2_PLAIN)

# field5 = int(arus_masuk * 1000) * 100000 + int(arus_keluar * 1000)
_PACK_FACTOR = 100000
# Encoding hanya sahih selama arus_masuk < 21 A dan arus_keluar < 99 A. Di atas
# itu bagian atas dan bawah saling makan dan dua-duanya jadi sampah.
_MAX_IN_MILLI = 21000
_MAX_OUT_MILLI = 99000


def is_support_channel(label: Optional[str]) -> bool:
    """Kanal pendukung dikenali dari labelnya ('pendukung', 'support', 'channel 2', 'kanal 2', dsb)."""
    if not label:
        return False
    l = label.strip().lower()
    return (
        l in ("pendukung", "support", "2")
        or "pendukung" in l
        or "support" in l
        or "channel 2" in l
        or "channel2" in l
        or "channel_2" in l
        or "kanal 2" in l
        or "kanal2" in l
        or "kanal_2" in l
        or "ch 2" in l
        or "ch2" in l
        or l.endswith(" 2")
        or l.endswith("_2")
        or l.endswith("-2")
    )


def has_valve(layout: str) -> bool:
    """Hanya Node 1 yang punya valve; di Node 2 bit2/bit3 tidak pernah menyala."""
    return layout == LAYOUT_NODE1_PACKED


def get_actuator_field(layout: str) -> str:
    """Mendapatkan nama field ThingSpeak untuk status bitmask aktuator pada kanal pendukung.
    - Node 1 (node1_packed): field7 (karena field8 dipakai untuk Daya Beban Aktual)
    - Node 2 (node2_plain): field8 (sesuai firmware Node 2)
    """
    return "field7" if layout == LAYOUT_NODE1_PACKED else "field8"


def decode_packed_current(mentah: Any) -> Tuple[Optional[float], Optional[float]]:
    """Legacy helper: field5 Node 1 -> (arus_masuk, arus_keluar) dalam ampere.
    Dipertahankan untuk kompatibilitas data arsip lama.
    """
    if mentah is None:
        return None, None
    try:
        nilai = int(float(mentah))
    except (TypeError, ValueError):
        return None, None
    if nilai < 0:
        return None, None

    masuk_milli, keluar_milli = divmod(nilai, _PACK_FACTOR)
    if masuk_milli >= _MAX_IN_MILLI or keluar_milli >= _MAX_OUT_MILLI:
        return None, None

    return masuk_milli / 1000.0, keluar_milli / 1000.0


def extract_channel_fields(
    data: Dict[str, Any],
    *,
    layout: str = LAYOUT_DEFAULT,
    channel_label: Optional[str] = None,
) -> Dict[str, Any]:
    """field1..field8 mentah -> dict siap pakai.
    
    Firmware baru Node 1 dan Node 2 mengirimkan nilai float/angka langsung
    di setiap field tanpa kompresi. Field yang tidak ada atau null dilewati.
    """
    hasil: Dict[str, Any] = {}

    for i in range(1, 9):
        nama = f"field{i}"
        if nama not in data or data[nama] is None:
            continue

        try:
            hasil[nama] = float(data[nama])
        except (TypeError, ValueError):
            hasil[nama] = data[nama]

    return hasil

