from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Literal
from app.core.database import get_db
from app.core.config import settings
from app.models.system_config import SystemConfig
from sqlalchemy import select
from app.repositories import node_repo, channel_repo, sensor_repo
from app.schemas.telemetry import DashboardSummaryResponse, SensorMetricSummary
from app.services.websocket_manager import manager
from datetime import datetime, timezone
from pydantic import BaseModel
import httpx
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

HISTORY_CACHE = {}
router = APIRouter()

@router.get("/nodes/{node_id}/telemetry/latest")
async def get_latest_telemetry(
    node_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_current_user)
):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
        
    cache_key = f"latest_{node_id}"
    now = time.time()
    if cache_key in HISTORY_CACHE:
        cached_time, cached_data = HISTORY_CACHE[cache_key]
        if now - cached_time < 15:
            return cached_data
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
    
    for result in results:
        if isinstance(result, Exception):
            continue
        channel, data = result
        if data:
            ch_uuid = str(channel.id)
            for i in range(1, 9):
                field_key = f"field{i}"
                if field_key in data and data[field_key] is not None:
                    merged_data[f"{ch_uuid}_{field_key}"] = data[field_key]
            
            ts = data.get("created_at")
            if ts:
                if latest_ts is None or ts > latest_ts:
                    latest_ts = ts
                    
    if not merged_data:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="ThingSpeak unavailable or no data")

    merged_data["created_at"] = latest_ts
    HISTORY_CACHE[cache_key] = (now, merged_data)
    return merged_data


@router.get("/nodes/{node_id}/telemetry/history")
async def get_history_telemetry(
    node_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_current_user),
    time_range: Optional[Literal["1h", "1d", "1w", "1M"]] = Query(None, alias="range", description="Preset range shortcut: 1h, 1d, 1w, 1M"),
    start: Optional[str] = Query(None, description="Start datetime in ISO 8601, e.g. 2026-08-01T00:00:00"),
    end: Optional[str] = Query(None, description="End datetime in ISO 8601, e.g. 2026-08-18T23:59:59"),
    results: Optional[int] = Query(None, ge=1, le=8000, description="Max number of results (ThingSpeak cap: 8000)"),
    average: Optional[int] = Query(None, ge=1, le=1440, description="Aggregate: average per N minutes (e.g. 10, 60)")
):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    # -------------------------------------------------------------
    # 🚀 HOT PATH: In-Memory Ring Buffer (1h, 1d / Live 24 Hours)
    # -------------------------------------------------------------
    is_hot_path = time_range in ("1h", "1d", None) and not (start or end)
    if is_hot_path:
        duration_hrs = 1.0 if time_range == "1h" else 24.0
        hot_data = get_hot_path_history(node_id, duration_hours=duration_hrs)
        
        # If hot buffer is already populated in memory, return immediately (<1ms)!
        if hot_data is not None and len(hot_data) > 0:
            if results:
                hot_data = hot_data[-results:]
            return {
                "channel": {"name": node.name, "description": "Hot-Path In-Memory Buffer"},
                "feeds": hot_data
            }

    # -------------------------------------------------------------
    # ❄️ COLD PATH & INITIAL BUFFER SEEDING: Serialized via Lock
    # -------------------------------------------------------------
    cache_key = f"{node_id}_{time_range}_{start}_{end}_{results}_{average}"
    now = time.time()
    if cache_key in HISTORY_CACHE:
        cached_time, cached_data = HISTORY_CACHE[cache_key]
        if now - cached_time < 15:
            return cached_data

    channels = await channel_repo.get_by_node_id(db, node.id)
    if not channels:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channels not configured for node")

    async with thingspeak_cold_lock:
        # Check cache once more after acquiring lock
        now = time.time()
        if cache_key in HISTORY_CACHE:
            cached_time, cached_data = HISTORY_CACHE[cache_key]
            if now - cached_time < 15:
                return cached_data

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
                        
                    # Add fields with channel prefix
                    for i in range(1, 9):
                        field_key = f"field{i}"
                        if field_key in feed and feed[field_key] is not None:
                            merged_feeds[rounded_ts][f"{ch_uuid}_{field_key}"] = feed[field_key]
                            
            # Sort by timestamp
            sorted_feeds = [merged_feeds[ts] for ts in sorted(merged_feeds.keys())]
            
            # Forward fill missing fields
            last_known = {}
            for feed in sorted_feeds:
                for key, value in feed.items():
                    if key != "created_at":
                        last_known[key] = value
                for key, value in last_known.items():
                    if key not in feed:
                        feed[key] = value
            
            if is_hot_path and sorted_feeds:
                set_initial_history(node_id, sorted_feeds)

            HISTORY_CACHE[cache_key] = (now, {"channel": {"name": node.name, "description": "Merged channels"}, "feeds": sorted_feeds})
            return HISTORY_CACHE[cache_key][1]

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
    db: AsyncSession = Depends(get_db)
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
        hist = await get_history_telemetry(node_id, db, current_user, time_range="1d")
        if isinstance(hist, dict) and "feeds" in hist:
            history_feeds = hist["feeds"]
    except Exception:
        history_feeds = []
        
    # Compute min/max map across all feeds
    field_stats: dict[str, dict] = {}
    for feed in history_feeds:
        for k, v in feed.items():
            if k in ("created_at", "entry_id") or v is None:
                continue
            try:
                val = float(v)
                if val <= -50 or val >= 20000:
                    continue
                if k not in field_stats:
                    field_stats[k] = {"min": val, "max": val, "values": [val]}
                else:
                    if val < field_stats[k]["min"]:
                        field_stats[k]["min"] = val
                    if val > field_stats[k]["max"]:
                        field_stats[k]["max"] = val
                    field_stats[k]["values"].append(val)
            except (ValueError, TypeError):
                continue
                
    # Build list of SensorMetricSummary
    summaries: list[SensorMetricSummary] = []
    for s in sensors:
        field_key = f"{s.channel_id}_{s.thingspeak_field}"
        curr_val_raw = latest_data.get(field_key)
        curr_val = None
        if curr_val_raw is not None:
            try:
                curr_val = round(float(curr_val_raw), 2)
            except (ValueError, TypeError):
                curr_val = None
        
        # Fallback forward-fill from history_feeds if latest packet omitted this field
        if curr_val is None and history_feeds:
            for feed in reversed(history_feeds):
                fallback_raw = feed.get(field_key)
                if fallback_raw is not None:
                    try:
                        curr_val = round(float(fallback_raw), 2)
                        break
                    except (ValueError, TypeError):
                        pass
                
        stats = field_stats.get(field_key, {})
        min_rec = round(stats["min"], 2) if "min" in stats else (curr_val if curr_val is not None else None)
        max_rec = round(stats["max"], 2) if "max" in stats else (curr_val if curr_val is not None else None)
        
        # Determine status
        status_val = "normal"
        if curr_val is not None:
            if s.min_threshold is not None and curr_val < s.min_threshold:
                status_val = "low"
            elif s.max_threshold is not None and curr_val > s.max_threshold:
                status_val = "high"
            else:
                status_val = "ideal" if s.type in ("nitrogen", "phosphorus", "potassium", "npk") else "normal"
                
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
            status=status_val
        )
        summaries.append(metric)
        
    # Categorization
    npk_sensors = []
    soil_probes = []
    soil_metrics = {}
    iot_metrics = {}
    
    for m in summaries:
        name_lower = m.name.lower()
        type_lower = m.type.lower()
        
        # NPK
        if any(k in name_lower or k in type_lower for k in ("nitrogen", "phosphorus", "fosfor", "potassium", "kalium")):
            npk_sensors.append(m)
        # Soil Probes
        elif "probe" in name_lower and ("soil" in name_lower or "titik" in name_lower or "1" in name_lower or "2" in name_lower or "3" in name_lower):
            soil_probes.append(m)
        # Soil Other Metrics
        elif "ph" in name_lower or type_lower == "ph":
            soil_metrics["ph"] = m
        elif "suhu tanah" in name_lower or "soil temp" in name_lower or type_lower == "soil_temperature":
            soil_metrics["soil_temp"] = m
        elif "ec" in name_lower or "conductivity" in name_lower or type_lower == "ec":
            soil_metrics["ec"] = m
        elif "rata-rata kelembapan" in name_lower or "avg moisture" in name_lower:
            soil_metrics["avg_moisture"] = m
        # IoT / Enclosure Metrics
        elif ("suhu dalam" in name_lower or "dalam casing" in name_lower or "enclosure" in name_lower) and "luar" not in name_lower:
            iot_metrics["enclosure_temp"] = m
        elif "suhu luar" in name_lower or "luar casing" in name_lower or "ambient" in name_lower or type_lower == "air_temperature":
            iot_metrics["air_temp"] = m
        elif "lembab luar" in name_lower or "kelembaban udara" in name_lower or "humidity" in name_lower or type_lower == "humidity":
            iot_metrics["humidity"] = m
        elif "modbus" in name_lower or "error" in name_lower:
            iot_metrics["modbus"] = m
            
    # Sort soil probes probe 1, probe 2, probe 3
    soil_probes.sort(key=lambda p: p.name)
    
    return DashboardSummaryResponse(
        node_id=node.node_id,
        node_name=node.name,
        last_seen=latest_data.get("created_at") or (node.last_seen.isoformat() if node.last_seen else None),
        is_active=node.is_active,
        sensors=summaries,
        npk_sensors=npk_sensors,
        soil_probes=soil_probes,
        soil_metrics=soil_metrics,
        iot_metrics=iot_metrics
    )
