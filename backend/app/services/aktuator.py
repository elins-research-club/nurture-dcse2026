"""Dekode status aktuator dari field8 kanal pendukung.

Firmware memampatkan tiga aktuator (Kipas, Lampu, Valve) jadi satu
angka 0-7 (3-bit bitmask), karena ThingSpeak cuma memberi delapan slot field per kanal.
"""

BIT_KIPAS = 0b0001
BIT_LAMPU = 0b0010
BIT_VALVE = 0b0100


def baca_aktuator(mentah) -> dict | None:
    """Bitmask -> status bernama. None kalau kosong atau di luar 0-7."""
    if mentah is None:
        return None
    try:
        nilai = int(float(mentah))
    except (TypeError, ValueError):
        return None
    if not 0 <= nilai <= 7:
        # Firmware memakai 3 bit (0-7). Nilai di luar itu berarti field8 rusak.
        return None
    return {
        "kipas": bool(nilai & BIT_KIPAS),
        "lampu": bool(nilai & BIT_LAMPU),
        "valve": bool(nilai & BIT_VALVE),
    }
