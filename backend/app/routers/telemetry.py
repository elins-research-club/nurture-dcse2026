from collections import OrderedDict
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, Optional, Literal
from app.core.database import get_db
from app.core.config import settings
from app.repositories import node_repo, channel_repo, sensor_repo
from app.schemas.telemetry import DashboardSummaryResponse, SensorMetricSummary
from app.services.websocket_manager import manager
from app.services import soil_health
from app.services.aktuator import baca_aktuator
from app.services.power_system import hitung_metrik_daya
from app.services.field_decoder import (
    LAYOUT_DEFAULT,
    extract_channel_fields,
    get_actuator_field,
    has_valve,
    is_support_channel,
)
from datetime import datetime, timezone
from pydantic import BaseModel
import asyncio
from dateutil.parser import isoparse

class TelemetryInject(BaseModel):
    temperature: float
    humidity: float
    soil_moisture: float
    battery_level: float

from app.dependencies.auth import get_current_user, get_optional_current_user

from app.services.telemetry_buffer import (
    get_hot_path_history,
    set_initial_history,
    thingspeak_cold_lock
)
from app.services.thingspeak_poller import get_http_client
import time

# Kunci cache ikut rentang tanggal kustom, jadi jumlahnya tidak terbatas kalau
# dibiarkan. Dict biasa di sini tumbuh terus selama proses hidup.
HISTORY_CACHE: "OrderedDict[str, tuple]" = OrderedDict()
_CACHE_TTL_SECONDS = 15
_CACHE_MAX_ENTRIES = 256

# Penanda internal di dalam satu feed. Diawali garis bawah supaya gampang
# disaring dari perhitungan statistik dan ekspor.
KUNCI_BASI = "_stale_keys"


def _cache_get(key: str):
    entry = HISTORY_CACHE.get(key)
    if entry is None:
        return None
    disimpan_pada, data = entry
    if time.time() - disimpan_pada >= _CACHE_TTL_SECONDS:
        HISTORY_CACHE.pop(key, None)
        return None
    HISTORY_CACHE.move_to_end(key)
    return data


def _cache_put(key: str, data):
    HISTORY_CACHE[key] = (time.time(), data)
    HISTORY_CACHE.move_to_end(key)
    while len(HISTORY_CACHE) > _CACHE_MAX_ENTRIES:
        HISTORY_CACHE.popitem(last=False)


def _kunci_terukur(feed: Dict[str, Any]):
    """Kunci yang benar-benar berisi pengukuran, bukan metadata feed."""
    return [
        k for k in feed
        if k not in ("created_at", "entry_id") and not k.startswith("_")
    ]


router = APIRouter()

import uuid

async def _find_node(db: AsyncSession, node_id: str):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        try:
            u = uuid.UUID(node_id)
            node = await node_repo.get_by_id(db, u)
        except Exception:
            pass
    return node

@router.get("/nodes/{node_id}/telemetry/latest")
async def get_latest_telemetry(
    node_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_current_user)
):
    node = await _find_node(db, node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    cache_key = f"latest_{node_id}"
    tembolok = _cache_get(cache_key)
    if tembolok is not None:
        return tembolok

    channels = await channel_repo.get_by_node_id(db, node.id)
    if not channels:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channels not configured for node")

    async def fetch_channel_latest(channel):
        url = f"{settings.THINGSPEAK_BASE_URL}/channels/{channel.channel_id}/feeds/last.json"
        params = {"api_key": channel.read_api_key}
        client = get_http_client()
        resp = await client.get(url, params=params)
        if resp.status_code == 200:
            return channel, resp.json()
        return channel, None

    tasks = [fetch_channel_latest(c) for c in channels]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    merged_data = {}
    latest_ts = None
    aktuator = None
    layout = node.field_layout or LAYOUT_DEFAULT

    for result in results:
        if isinstance(result, Exception):
            continue
        channel, data = result
        if data:
            ch_uuid = str(channel.id)
            # Lewat decoder, bukan loop field mentah: kalau tidak, field5 Node 1
            # tetap satu angka terpampat dan Arus Input/Output selamanya kosong.
            for nama_field, nilai in extract_channel_fields(
                data, layout=layout, channel_label=channel.label
            ).items():
                merged_data[f"{ch_uuid}_{nama_field}"] = nilai

            if is_support_channel(channel.label):
                actuator_f = get_actuator_field(layout)
                if data.get(actuator_f) is not None:
                    aktuator = baca_aktuator(data.get(actuator_f), punya_valve=has_valve(layout))

            ts = data.get("created_at")
            if ts:
                if latest_ts is None or ts > latest_ts:
                    latest_ts = ts

    if not merged_data:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="ThingSpeak unavailable or no data")

    merged_data["created_at"] = latest_ts
    # Status aktuator ikut supaya kartu langsung tampil saat halaman dibuka,
    # tidak menunggu pesan WebSocket berikutnya.
    merged_data["_aktuator"] = aktuator
    _cache_put(cache_key, merged_data)
    return merged_data


@router.get("/nodes/{node_id}/telemetry/history")
@router.get("/telemetry/history")
async def get_history_telemetry(
    node_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_current_user),
    time_range: Optional[Literal["1h", "1d", "1w", "1M"]] = Query(None, alias="range", description="Preset range shortcut: 1h, 1d, 1w, 1M"),
    start: Optional[str] = Query(None, description="Start datetime in ISO 8601, e.g. 2026-08-01T00:00:00"),
    end: Optional[str] = Query(None, description="End datetime in ISO 8601, e.g. 2026-08-18T23:59:59"),
    results: Optional[int] = Query(None, ge=1, le=8000, description="Max number of results (ThingSpeak cap: 8000)"),
    average: Optional[int] = Query(None, ge=1, le=1440, description="Aggregate: average per N minutes (e.g. 10, 60)")
):
    # Sanitize parameters if called directly as a Python function (not via FastAPI dependency injection)
    if not isinstance(time_range, str):
        time_range = None
    if not isinstance(start, str):
        start = None
    if not isinstance(end, str):
        end = None
    if not isinstance(results, int):
        results = None
    if not isinstance(average, int):
        average = None

    if not node_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="node_id is required")
    node = await _find_node(db, node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    # -------------------------------------------------------------
    # HOT PATH: In-Memory Ring Buffer (1h, 1d / Live 24 Hours)
    # -------------------------------------------------------------
    is_hot_path = time_range in ("1h", "1d", None) and not (start or end) and not average
    if is_hot_path:
        duration_hrs = 1.0 if time_range == "1h" else 24.0
        hot_data = get_hot_path_history(node_id, duration_hours=duration_hrs)

        if hot_data is not None and len(hot_data) > 0:
            if results:
                hot_data = hot_data[-results:]
            return {
                "channel": {"name": node.name, "description": "Hot-Path In-Memory Buffer"},
                "feeds": hot_data
            }

    # -------------------------------------------------------------
    # COLD PATH & INITIAL BUFFER SEEDING: Serialized via Lock
    # -------------------------------------------------------------
    cache_key = f"{node_id}_{time_range}_{start}_{end}_{results}_{average}"
    tembolok = _cache_get(cache_key)
    if tembolok is not None:
        return tembolok

    channels = await channel_repo.get_by_node_id(db, node.id)
    if not channels:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channels not configured for node")

    layout = node.field_layout or LAYOUT_DEFAULT

    async with thingspeak_cold_lock:
        # Check cache once more after acquiring lock
        tembolok = _cache_get(cache_key)
        if tembolok is not None:
            return tembolok

        # Build ThingSpeak base params
        base_params = {}
        if time_range == "1h":
            base_params["minutes"] = 60
        elif time_range == "1d":
            base_params["hours"] = 24
        elif time_range == "1w":
            base_params["days"] = 7
        elif time_range == "1M":
            base_params["days"] = 30
        elif start or end:
            if start:
                base_params["start"] = start
            if end:
                base_params["end"] = end
            if results:
                base_params["results"] = results
        else:
            base_params["results"] = results or 100

        if average:
            base_params["average"] = average

        async def fetch_channel_history(channel):
            params = base_params.copy()
            params["api_key"] = channel.read_api_key
            url = f"{settings.THINGSPEAK_BASE_URL}/channels/{channel.channel_id}/feeds.json"

            client = get_http_client()
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                return channel, resp.json()
            elif resp.status_code == 429:
                raise HTTPException(status_code=429, detail="ThingSpeak rate limit exceeded")
            else:
                return channel, None

        tasks = [fetch_channel_history(c) for c in channels]
        fetch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge histories
        try:
            merged_feeds = {}

            for result in fetch_results:
                if isinstance(result, Exception):
                    if isinstance(result, HTTPException):
                        raise result
                    continue

                channel, data = result
                if not data or "feeds" not in data:
                    continue

                ch_uuid = str(channel.id)
                for feed in data["feeds"]:
                    ts_str = feed.get("created_at")
                    if not ts_str:
                        continue

                    # Parse and round timestamp to nearest 15 seconds to merge channels
                    try:
                        dt = isoparse(ts_str)
                        rounded_ts = int(dt.timestamp()) // 15 * 15
                    except Exception:
                        continue

                    if rounded_ts not in merged_feeds:
                        merged_feeds[rounded_ts] = {"created_at": ts_str}

                    # Field null DILEWATI, bukan dijadikan nol -- firmware memang
                    # menghilangkan field saat pembacaan gagal. Lewat decoder juga
                    # supaya field5 Node 1 terbongkar jadi field5_in/field5_out.
                    for nama_field, nilai in extract_channel_fields(
                        feed, layout=layout, channel_label=channel.label
                    ).items():
                        merged_feeds[rounded_ts][f"{ch_uuid}_{nama_field}"] = nilai

            # Sort by timestamp
            sorted_feeds = [merged_feeds[ts] for ts in sorted(merged_feeds.keys())]

            # Forward fill missing fields.
            #
            # Ini menutup lubang transien Modbus supaya grafik tidak putus, tapi
            # hasilnya TIDAK boleh terlihat sama dengan pembacaan baru: nilai yang
            # disalin dicatat di KUNCI_BASI agar frontend bisa menandainya. Tanpa
            # catatan itu, "tidak ada pembacaan" berubah diam-diam jadi angka.
            last_known: Dict[str, Any] = {}
            for feed in sorted_feeds:
                for key in _kunci_terukur(feed):
                    last_known[key] = feed[key]
                disalin = [k for k in last_known if k not in feed]
                for key in disalin:
                    feed[key] = last_known[key]
                if disalin:
                    feed[KUNCI_BASI] = disalin

            if is_hot_path and sorted_feeds:
                set_initial_history(node_id, sorted_feeds)

            hasil = {"channel": {"name": node.name, "description": "Merged channels"}, "feeds": sorted_feeds}
            _cache_put(cache_key, hasil)
            return hasil

        except HTTPException:
            raise

        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/nodes/{node_id}/telemetry/inject")
async def inject_telemetry(
    node_id: str,
    data: TelemetryInject,
    db: AsyncSession = Depends(get_db),
    # Endpoint ini menyiarkan apa saja ke semua klien WebSocket. Tanpa auth,
    # siapa pun yang bisa menjangkau port backend bisa memalsukan telemetri.
    current_user = Depends(get_current_user),
):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    telemetry_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "temperature": data.temperature,
        "humidity": data.humidity,
        "soil_moisture": data.soil_moisture,
        "battery_level": data.battery_level
    }

    payload = {
        "type": "telemetry",
        "node_id": node.node_id,
        "data": telemetry_data
    }

    await manager.broadcast_all(payload)
    return {"status": "success", "message": "Telemetry injected and broadcasted"}


# --- Pengenalan peran sensor ------------------------------------------------
# Baris sensor lama memakai type generik ("soil", "environment"), sedangkan seed
# baru memakai type spesifik. Jadi type diperiksa dulu, nama jadi cadangan.

def _peran_sensor(s) -> Optional[str]:
    t = (s.type or "").lower()
    n = (s.name or "").lower()

    if t in ("ph", "soil_ph") or n == "ph" or n.startswith("ph ") or "keasaman" in n:
        return "ph"
    if t in ("ec", "soil_ec") or "conductivity" in n or n == "ec" or n.startswith("ec "):
        return "ec"
    if t in ("soil_temperature", "soil_temp") or "suhu tanah" in n or "soil temp" in n:
        return "soil_temperature"
    if t in ("soil_probe", "soil_moisture_probe") or "probe analog" in n or "soil probe" in n:
        return "soil_probe"
    if t in ("avg_soil_moisture", "soil_moisture") or "rata-rata kelembapan" in n:
        return "soil_moisture"
    if "nitrogen" in n or t in ("nitrogen", "npk_n"):
        return "nitrogen"
    if "fosfor" in n or "phosphor" in n or t in ("phosphorus", "npk_p"):
        return "phosphorus"
    if "kalium" in n or "potassium" in n or t in ("potassium", "npk_k"):
        return "potassium"
    # Daya & Baterai INA226
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
    # Fallback legacy
    if t == "batt_volt":
        return "tegangan_in" if s.thingspeak_field in ("field2", "field3") else "tegangan_out"
    if t == "current":
        return "arus_in" if s.thingspeak_field in ("field4", "field5", "field5_in") else "arus_out"
    if t in ("probe_moist", "npk_moisture"):
        return "lengas_npk"
    return None


@router.get("/nodes/{node_id}/telemetry/dashboard", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    node_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_current_user)
):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    sensors = await sensor_repo.list_by_node(db, node.id, skip=0, limit=100)

    # 1. Fetch latest telemetry
    latest_data = {}
    try:
        latest_data = await get_latest_telemetry(node_id, db, current_user)
    except Exception:
        latest_data = {}

    # 2. Fetch 24h history for min/max calculations
    history_feeds = []
    try:
        hist = await get_history_telemetry(
            node_id=node_id, 
            db=db, 
            current_user=current_user, 
            time_range="1d",
            start=None,
            end=None,
            results=None,
            average=None,
        )
        if isinstance(hist, dict) and "feeds" in hist:
            history_feeds = hist["feeds"]
    except Exception:
        history_feeds = []

    # Compute min/max map across all feeds. Nilai hasil forward-fill dilewati
    # supaya satu pembacaan tidak dihitung berkali-kali sebagai min/maks.
    field_stats: dict[str, dict] = {}
    for feed in history_feeds:
        basi = set(feed.get(KUNCI_BASI) or ())
        for k in _kunci_terukur(feed):
            if k in basi:
                continue
            v = feed[k]
            if v is None:
                continue
            try:
                val = float(v)
                if val <= -50 or val >= 20000:
                    continue
                if k not in field_stats:
                    field_stats[k] = {"min": val, "max": val}
                else:
                    if val < field_stats[k]["min"]:
                        field_stats[k]["min"] = val
                    if val > field_stats[k]["max"]:
                        field_stats[k]["max"] = val
            except (ValueError, TypeError):
                continue

    # Build list of SensorMetricSummary
    summaries: list[SensorMetricSummary] = []
    nilai_per_peran: dict[str, float] = {}
    lengas_probe: list[float] = []

    for s in sensors:
        field_key = f"{s.channel_id}_{s.thingspeak_field}"
        curr_val_raw = latest_data.get(field_key)
        curr_val = None
        is_stale = False
        reading_at = latest_data.get("created_at")

        if curr_val_raw is not None:
            try:
                curr_val = round(float(curr_val_raw), 2)
            except (ValueError, TypeError):
                curr_val = None

        # Fallback forward-fill kalau paket terbaru memang tidak membawa field
        # ini. Ditandai basi supaya angka lama tidak menyamar jadi angka baru.
        if curr_val is None and history_feeds:
            for feed in reversed(history_feeds):
                fallback_raw = feed.get(field_key)
                if fallback_raw is None:
                    continue
                try:
                    curr_val = round(float(fallback_raw), 2)
                    is_stale = True
                    reading_at = feed.get("created_at")
                    break
                except (ValueError, TypeError):
                    continue

        if curr_val is None:
            reading_at = None

        stats = field_stats.get(field_key, {})
        min_rec = round(stats["min"], 2) if "min" in stats else (curr_val if curr_val is not None else None)
        max_rec = round(stats["max"], 2) if "max" in stats else (curr_val if curr_val is not None else None)

        # Status di sini adalah ambang OPERATOR dari database, bukan kelas
        # pustaka. Klasifikasi terhadap standar terbit ada di soil_health.
        status_val = "unknown"
        if curr_val is not None:
            if s.min_threshold is not None and curr_val < s.min_threshold:
                status_val = "low"
            elif s.max_threshold is not None and curr_val > s.max_threshold:
                status_val = "high"
            else:
                status_val = "normal"

        metric = SensorMetricSummary(
            id=s.id,
            name=s.name,
            type=s.type,
            unit=s.unit,
            thingspeak_field=s.thingspeak_field,
            channel_id=s.channel_id,
            field_key=field_key,
            current_value=curr_val,
            min_recorded=min_rec,
            max_recorded=max_rec,
            min_threshold=s.min_threshold,
            max_threshold=s.max_threshold,
            status=status_val,
            is_stale=is_stale,
            reading_at=reading_at,
        )
        summaries.append(metric)

        peran = _peran_sensor(s)
        if peran and curr_val is not None:
            if peran == "soil_moisture":
                lengas_probe.append(curr_val)
            else:
                nilai_per_peran.setdefault(peran, curr_val)

    # Categorization
    npk_sensors = []
    soil_probes = []
    soil_metrics = {}
    iot_metrics = {}

    for m in summaries:
        name_lower = m.name.lower()
        type_lower = m.type.lower()
        # NPK
        if any(k in name_lower or k in type_lower for k in ("nitrogen", "phosphorus", "phosphor", "phospor", "fosfor", "potassium", "kalium")):
            npk_sensors.append(m)
        elif "probe" in name_lower and ("soil" in name_lower or "tanah" in name_lower or "titik" in name_lower):
            soil_probes.append(m)
        elif "ph" in name_lower or type_lower in ("ph", "soil_ph"):
            soil_metrics["ph"] = m
        elif "suhu tanah" in name_lower or "soil temp" in name_lower or type_lower in ("soil_temp", "soil_temperature"):
            soil_metrics["soil_temp"] = m
        elif "ec" in name_lower or "conductivity" in name_lower or type_lower in ("ec", "soil_ec"):
            soil_metrics["ec"] = m
        elif "rata-rata kelembapan" in name_lower or "avg moisture" in name_lower or type_lower in ("avg_soil_moisture", "soil_moisture"):
            soil_metrics["avg_moisture"] = m
        elif ("suhu dalam" in name_lower or "dalam casing" in name_lower or "box panel" in name_lower or "enclosure" in name_lower) and "luar" not in name_lower:
            iot_metrics["enclosure_temp"] = m
        elif "suhu luar" in name_lower or "luar casing" in name_lower or "ambient" in name_lower or "suhu udara" in name_lower or type_lower in ("air_temp", "air_temperature"):
            iot_metrics["air_temp"] = m
        elif "lembab luar" in name_lower or "kelembapan udara" in name_lower or "kelembaban udara" in name_lower or "humidity" in name_lower or type_lower in ("air_humidity", "humidity"):
            iot_metrics["humidity"] = m
        elif "daya" in name_lower or type_lower in ("load_power", "power"):
            iot_metrics["power"] = m
        elif "modbus" in name_lower or "error" in name_lower:
            iot_metrics["modbus"] = m

    soil_probes.sort(key=lambda p: p.name)

    # Rata-rata lengas:
    # 1. Dari field rata-rata kelembapan tanah firmware (Node 1 Ch1 field6)
    # 2. Rata-rata dari probe analog individual (jika ada)
    # 3. Lengas dari probe NPK Modbus (Node 2 Ch2 field2)
    if nilai_per_peran.get("soil_moisture") is not None:
        rerata_lengas = nilai_per_peran["soil_moisture"]
        sumber_lengas = "rata-rata kelembapan tanah (firmware)"
    elif lengas_probe:
        rerata_lengas = round(sum(lengas_probe) / len(lengas_probe), 1)
        sumber_lengas = f"rata-rata {len(lengas_probe)} probe analog"
    elif nilai_per_peran.get("lengas_npk") is not None:
        rerata_lengas = nilai_per_peran["lengas_npk"]
        sumber_lengas = "probe NPK (Node 2)"
    else:
        rerata_lengas = None
        sumber_lengas = None

    # Sistem Solar Panel (INA226): disintesis melalui service terpusat power_system
    power_metrics = hitung_metrik_daya(
        tegangan_in=nilai_per_peran.get("tegangan_in"),
        arus_in=nilai_per_peran.get("arus_in"),
        tegangan_out=nilai_per_peran.get("tegangan_out"),
        arus_out=nilai_per_peran.get("arus_out"),
        daya_out_langsung=nilai_per_peran.get("daya_out"),
        node_id=node.node_id,
    )

    vonis = soil_health.nilai_kesehatan_tanah(
        ph=nilai_per_peran.get("ph"),
        ec_us_cm=nilai_per_peran.get("ec"),
        lengas_persen=rerata_lengas,
        suhu_tanah=nilai_per_peran.get("soil_temperature"),
        nitrogen=nilai_per_peran.get("nitrogen"),
        fosfor=nilai_per_peran.get("phosphorus"),
        kalium=nilai_per_peran.get("potassium"),
        # Kerapatan isi belum diukur di lapangan, jadi WFPS sengaja tidak
        # dihitung. Isi nilainya di sini kalau sudah ada data bulk density.
        kerapatan_isi=None,
    )

    return DashboardSummaryResponse(
        aktuator=latest_data.get("_aktuator"),
        node_id=node.node_id,
        node_name=node.name,
        last_seen=latest_data.get("created_at") or (node.last_seen.isoformat() if node.last_seen else None),
        is_active=node.is_active,
        sensors=summaries,
        npk_sensors=npk_sensors,
        soil_probes=soil_probes,
        soil_metrics=soil_metrics,
        iot_metrics=iot_metrics,
        power_metrics=power_metrics,
        soil_health=vonis,
    )
