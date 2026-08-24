from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Literal
from app.core.database import get_db
from app.core.config import settings
from app.models.system_config import SystemConfig
from sqlalchemy import select
from app.repositories import node_repo, channel_repo
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

# Attempt to import get_current_user if auth is implemented, else create a dummy dependency
try:
    from app.dependencies.auth import get_current_user
except ImportError:
    async def get_current_user():
        return None

import time

HISTORY_CACHE = {}
router = APIRouter()

@router.get("/nodes/{node_id}/telemetry/latest")
async def get_latest_telemetry(
    node_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
        
    
    sys_conf_result = await db.execute(select(SystemConfig).filter_by(id=1))
    sys_conf = sys_conf_result.scalars().first()
    cache_ttl = sys_conf.telemetry_cache_interval if sys_conf else 30

    cache_key = f"{node_id}_{time_range}_{start}_{end}_{results}"
    now = time.time()
    if cache_key in HISTORY_CACHE:
        cached_time, cached_data = HISTORY_CACHE[cache_key]
        if now - cached_time < cache_ttl:
            return cached_data
    channels = await channel_repo.get_by_node_id(db, node.id)
    if not channels:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channels not configured for node")
        
    async def fetch_channel_latest(channel):
        url = f"{settings.THINGSPEAK_BASE_URL}/channels/{channel.channel_id}/feeds/last.json"
        params = {"api_key": channel.read_api_key}
        async with httpx.AsyncClient(timeout=10.0) as client:
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
    return merged_data


@router.get("/nodes/{node_id}/telemetry/history")
async def get_history_telemetry(
    node_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    time_range: Optional[Literal["1h", "1d", "1w", "1M"]] = Query(None, alias="range", description="Preset range shortcut: 1h, 1d, 1w, 1M"),
    start: Optional[str] = Query(None, description="Start datetime in ISO 8601, e.g. 2026-08-01T00:00:00"),
    end: Optional[str] = Query(None, description="End datetime in ISO 8601, e.g. 2026-08-18T23:59:59"),
    results: Optional[int] = Query(None, ge=1, le=8000, description="Max number of results (ThingSpeak cap: 8000)"),
    average: Optional[int] = Query(None, ge=1, le=1440, description="Aggregate: average per N minutes (e.g. 10, 60)")
):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    
    sys_conf_result = await db.execute(select(SystemConfig).filter_by(id=1))
    sys_conf = sys_conf_result.scalars().first()
    cache_ttl = sys_conf.telemetry_cache_interval if sys_conf else 30

    cache_key = f"{node_id}_{time_range}_{start}_{end}_{results}_{average}"
    now = time.time()
    if cache_key in HISTORY_CACHE:
        cached_time, cached_data = HISTORY_CACHE[cache_key]
        if now - cached_time < cache_ttl:
            return cached_data
    channels = await channel_repo.get_by_node_id(db, node.id)
    if not channels:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channels not configured for node")

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
        
        async with httpx.AsyncClient(timeout=15.0) as client:
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
    # To merge properly for a time-series chart, we can group by timestamps that are close together,
    # but the simplest way is to return all data points and let the frontend plot them, 
    # OR we merge them into a single array of points sorted by time.
    # Since ThingSpeak channels can be updated at slightly different ms, we will round to nearest 10 seconds.
    
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
                    # Round down to nearest 15s window
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
        
        # Forward fill missing fields so that sensors from different channels
        # that are slightly desynced will always carry over their last known value.
        last_known = {}
        for feed in sorted_feeds:
            for key, value in feed.items():
                if key != "created_at":
                    last_known[key] = value
            for key, value in last_known.items():
                if key not in feed:
                    feed[key] = value
        
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
