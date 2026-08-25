"""Dekode status aktuator dari field8 kanal pendukung.

Firmware memampatkan tiga aktuator dan satu penanda gangguan jadi satu
angka 0-15, karena ThingSpeak cuma memberi delapan slot field per kanal.
"""

BIT_KIPAS = 0b0001
BIT_LAMPU = 0b0010
BIT_VALVE = 0b0100
BIT_VALVE_TIMEOUT = 0b1000


def baca_aktuator(mentah) -> dict | None:
    """Bitmask -> status bernama. None kalau kosong atau di luar 0-15."""
    if mentah is None:
        return None
    try:
        nilai = int(float(mentah))
    except (TypeError, ValueError):
        return None
    if not 0 <= nilai <= 15:
        # Firmware hanya memakai 4 bit. Nilai di luar itu berarti field8
        # rusak, dan menerimanya menghasilkan status yang kelihatan wajar --
        # 200 misalnya terbaca sebagai valve_timeout menyala sendirian.
        return None
    return {
        "kipas": bool(nilai & BIT_KIPAS),
        "lampu": bool(nilai & BIT_LAMPU),
        "valve": bool(nilai & BIT_VALVE),
        "valve_timeout": bool(nilai & BIT_VALVE_TIMEOUT),
    }
