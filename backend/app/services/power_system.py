"""Modul kalkulasi dan sintesis metrik Sistem Solar Panel (INA226 & Solar Panel).

Mengisolasi seluruh logika bisnis kelistrikan dari frontend:
1. Normalisasi tegangan (V) dan arus (A) untuk baterai dan beban sistem.
2. Perhitungan daya masuk (daya_in = V_in x I_in) dan daya keluar (daya_out).
3. Perhitungan aliran daya netto (net_power) dan klasifikasi status energi:
   - "surplus" / "Surplus Solar" : Panel surya menghasilkan daya berlebih untuk mengisi aki/baterai.
   - "standby" / "Float / Siaga" : Arus baterai di sekitar 0 (daya seimbang / tidak ada pengisian signifikan).
   - "defisit" / "Defisit (Aki Aktif)" : Aki memasok beban karena tidak ada sinar matahari cukup.
   - "offline" / "Sensor Offline" : Data sensor INA226 tidak tersedia.
4. Estimasi persentase kapasitas aki 12V (11.5V - 13.8V -> 0% - 100%).
5. Deteksi keaktifan modul hardware I2C 0x40 (baterai) dan 0x41 (beban).
"""

from typing import Any, Dict, Optional, Tuple


def _parse_float(val: Any) -> Optional[float]:
    """Konversi nilai mentah menjadi float valid, atau None jika null/invalid."""
    if val is None:
        return None
    try:
        n = float(val)
        return n if (-1000.0 <= n <= 100000.0) else None
    except (ValueError, TypeError):
        return None


def hitung_metrik_daya(
    tegangan_in: Any,
    arus_in: Any,
    tegangan_out: Any,
    arus_out: Any,
    daya_out_langsung: Any = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Menghitung dan mensintesis seluruh status kelistrikan sistem dari pembacaan INA226.
    
    Args:
        tegangan_in: Tegangan baterai/input (Volt).
        arus_in: Arus baterai/input (Ampere).
        tegangan_out: Tegangan beban/output (Volt).
        arus_out: Arus beban/output (Ampere).
        daya_out_langsung: Daya beban aktual dari firmware (Watt) jika tersedia.
        node_id: Identifier node (opsional, untuk penyesuaian khusus node jika ada).

    Returns:
        Dict berisi parameter kelistrikan yang sudah dihitung dan siap dikonsumsi UI.
    """
    v_in = _parse_float(tegangan_in)
    a_in = _parse_float(arus_in)
    v_out = _parse_float(tegangan_out)
    a_out = _parse_float(arus_out)
    p_out_direct = _parse_float(daya_out_langsung)

    # 1. Perhitungan daya dasar (P = V x A)
    daya_in = round(v_in * a_in, 2) if (v_in is not None and a_in is not None) else None
    
    if p_out_direct is not None:
        daya_out = round(p_out_direct, 2)
    elif v_out is not None and a_out is not None:
        daya_out = round(v_out * a_out, 2)
    else:
        daya_out = None

    # 2. Deteksi status hardware I2C INA226
    i2c_0x40_active = v_in is not None and v_in > 0.5
    i2c_0x41_active = v_out is not None and v_out > 0.5

    # 3. Klasifikasi aliran daya & status pengisian aki berdasarkan daya fisik riil (P = V x A)
    if a_in is None or v_in is None:
        status_aliran = "offline"
        status_label = "Sensor Offline"
        battery_status_text = "Sensor Offline"
        is_charging = False
        is_standby = True
        net_power = None
    else:
        # Daya netto riil baterai: positif = arus masuk (charging), negatif = arus keluar (discharging)
        p_net = round(v_in * a_in, 2)
        net_power = p_net

        if p_net > 0:
            # Arus positif: Solar panel menyuplai beban dan surplus mengisi aki
            status_aliran = "surplus"
            status_label = "Surplus Solar"
            battery_status_text = "Solar Aktif (Mengisi Aki)"
            is_charging = True
            is_standby = False
        elif p_net < 0:
            # Arus negatif: Daya solar kurang/mati, aki aktif menyuplai beban
            status_aliran = "defisit"
            status_label = "Suplai Cadangan Aki"
            battery_status_text = "Tenaga Baterai (Solar Mati)"
            is_charging = False
            is_standby = False
        else:
            # Daya netto 0.0 W: baterai seimbang / tidak ada arus mengalir
            status_aliran = "standby"
            status_label = "Daya Seimbang"
            battery_status_text = "Daya Seimbang (Siaga)"
            is_charging = False
            is_standby = True

    # 4. Estimasi kapasitas baterai 12V (Aki Timbal / LiFePO4 buffer)
    # Rentang tegangan: 11.0V (0% habis total) sampai 13.8V (100% penuh)
    battery_level_percent: Optional[int] = None
    if v_in is not None:
        pct = round(((v_in - 11.0) / (13.8 - 11.0)) * 100)
        battery_level_percent = max(0, min(100, pct))

    return {
        "tegangan_in": v_in,
        "tegangan_out": v_out,
        "arus_in": a_in,
        "arus_out": a_out,
        "daya_in": daya_in,
        "daya_out": daya_out,
        "net_power": net_power,
        "status_aliran": status_aliran,
        "status_label": status_label,
        "battery_status_text": battery_status_text,
        "battery_level_percent": battery_level_percent,
        "is_charging": is_charging,
        "is_standby": is_standby,
        "i2c_0x40_active": i2c_0x40_active,
        "i2c_0x41_active": i2c_0x41_active,
        "satuan": {"tegangan": "V", "arus": "A", "daya": "W"},
        "catatan": "Dihitung di backend FastAPI berdasarkan data telemetri INA226.",
    }


def deteksi_peran_sensor_daya(sensor: Any) -> Optional[str]:
    """Mengidentifikasi peran sensor daya berdasarkan tipe atau nama sensor."""
    n = (getattr(sensor, "name", "") or "").lower()
    t = (getattr(sensor, "type", "") or "").lower()

    if t == "batt_volt" or ("baterai" in n and "tegangan" in n):
        return "tegangan_in"
    if t == "load_volt" or ("load" in n and "tegangan" in n):
        return "tegangan_out"
    if t == "batt_current" or ("baterai" in n and "arus" in n):
        return "arus_in"
    if t == "load_current" or ("load" in n and "arus" in n):
        return "arus_out"
    if t in ("load_power", "power") or "daya" in n:
        return "daya_out"
    return None


def ekstrak_dan_hitung_daya(sensors: list, data_dict: Dict[str, Any], node_id: Optional[str] = None) -> Dict[str, Any]:
    """Mengekstrak data mentah INA226 dari dictionary telemetri dan menghitung metrik daya."""
    nilai_daya: Dict[str, Any] = {}

    for s in sensors:
        peran = deteksi_peran_sensor_daya(s)
        if not peran:
            continue

        field_key = f"{s.channel_id}_{s.thingspeak_field}"
        if field_key in data_dict and data_dict[field_key] is not None:
            nilai_daya.setdefault(peran, data_dict[field_key])

    return hitung_metrik_daya(
        tegangan_in=nilai_daya.get("tegangan_in"),
        arus_in=nilai_daya.get("arus_in"),
        tegangan_out=nilai_daya.get("tegangan_out"),
        arus_out=nilai_daya.get("arus_out"),
        daya_out_langsung=nilai_daya.get("daya_out"),
        node_id=node_id,
    )

