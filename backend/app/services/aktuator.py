"""Dekode status aktuator dari field8 kanal pendukung.

Firmware memampatkan aktuator jadi satu bitmask, karena ThingSpeak cuma memberi
delapan slot field per kanal:

    bit0 kipas · bit1 lampu · bit2 valve · bit3 valve_timeout

Node 2 tidak punya valve, jadi bit2 dan bit3 di sana tidak pernah menyala --
maskanya sama, cuma bitnya mati. Karena itu `punya_valve` menentukan apakah
kunci valve ikut dilaporkan, bukan bagaimana angkanya dibaca.
"""

BIT_KIPAS = 0b0001
BIT_LAMPU = 0b0010
BIT_VALVE = 0b0100
BIT_VALVE_TIMEOUT = 0b1000

MASK_MAKS = 0b1111


def baca_aktuator(mentah, *, punya_valve: bool = True) -> dict | None:
    """Bitmask -> status bernama. None kalau kosong atau di luar 0-15.

    Batas atasnya 15, bukan 7. Firmware Node 1 mengirim bit3 (valve_timeout);
    dengan batas lama satu kali timeout membuat SELURUH pembacaan aktuator
    hilang, bukan cuma satu bit yang menyala.
    """
    if mentah is None:
        return None
    try:
        nilai = int(float(mentah))
    except (TypeError, ValueError):
        return None
    if not 0 <= nilai <= MASK_MAKS:
        # Firmware memakai 4 bit (0-15). Di luar itu berarti field8 rusak.
        return None

    status = {
        "kipas": bool(nilai & BIT_KIPAS),
        "lampu": bool(nilai & BIT_LAMPU),
    }
    if punya_valve:
        status["valve"] = bool(nilai & BIT_VALVE)
        status["valve_timeout"] = bool(nilai & BIT_VALVE_TIMEOUT)
    return status
