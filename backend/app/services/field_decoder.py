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
    """Kanal pendukung dikenali dari labelnya, sama seperti sebelumnya."""
    return (label or "").strip().lower() == "pendukung"


def has_valve(layout: str) -> bool:
    """Hanya Node 1 yang punya valve; di Node 2 bit2/bit3 tidak pernah menyala."""
    return layout == LAYOUT_NODE1_PACKED


def decode_packed_current(mentah: Any) -> Tuple[Optional[float], Optional[float]]:
    """field5 Node 1 -> (arus_masuk, arus_keluar) dalam ampere.

    Mengembalikan (None, None) kalau kosong, bukan angka, atau sudah melewati
    batas encoding. Lebih baik tidak ada pembacaan daripada dua angka yang
    kelihatan wajar tapi salah.
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
    """field1..field8 mentah -> dict siap pakai, sudah dibongkar sesuai layout.

    Field yang tidak ada atau null DILEWATI, bukan dijadikan nol. Firmware
    memang menghilangkan field saat pembacaan gagal; nol akan terbaca sebagai
    tanah yang benar-benar habis haranya.
    """
    hasil: Dict[str, Any] = {}
    dipampatkan = layout == LAYOUT_NODE1_PACKED and is_support_channel(channel_label)

    for i in range(1, 9):
        nama = f"field{i}"
        if nama not in data or data[nama] is None:
            continue

        if dipampatkan and nama == "field5":
            masuk, keluar = decode_packed_current(data[nama])
            if masuk is not None:
                hasil["field5_in"] = masuk
            if keluar is not None:
                hasil["field5_out"] = keluar
            continue

        try:
            hasil[nama] = float(data[nama])
        except (TypeError, ValueError):
            hasil[nama] = data[nama]

    return hasil
