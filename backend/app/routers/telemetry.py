from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Literal
from app.core.database import get_db
from app.core.config import settings
from app.repositories import node_repo, channel_repo
from app.services.thingspeak_poller import fetch_latest
from app.services.websocket_manager import manager
from datetime import datetime, timezone
from pydantic import BaseModel
import httpx

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
        
    channel = await channel_repo.get_by_node_id(db, node.id)
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not configured for node")
        
    data = await fetch_latest(channel.channel_id, channel.read_api_key)
    if data is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="ThingSpeak unavailable")
        
    return data

@router.get("/nodes/{node_id}/telemetry/history")
async def get_history_telemetry(
    node_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    range: Optional[Literal["1h", "1d", "1w"]] = Query(None, description="Preset range shortcut: 1h, 1d, 1w"),
    start: Optional[str] = Query(None, description="Start datetime in ISO 8601, e.g. 2026-08-01T00:00:00"),
    end: Optional[str] = Query(None, description="End datetime in ISO 8601, e.g. 2026-08-18T23:59:59"),
    results: int = Query(100, ge=1, le=8000, description="Max number of results (ThingSpeak cap: 8000)")
):
    node = await node_repo.get_by_node_id(db, node_id)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    channel = await channel_repo.get_by_node_id(db, node.id)
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not configured for node")

    # Build ThingSpeak params
    params: dict = {"api_key": channel.read_api_key}

    if range == "1h":
        params["minutes"] = 60
    elif range == "1d":
        params["hours"] = 24
    elif range == "1w":
        params["days"] = 7
    elif start or end:
        # Custom date range from datepicker
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        params["results"] = results
    else:
        # Default: last 100 entries
        params["results"] = results

    url = f"{settings.THINGSPEAK_BASE_URL}/channels/{channel.channel_id}/feeds.json"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                raise HTTPException(status_code=429, detail="ThingSpeak rate limit exceeded, try again later")
            else:
                raise HTTPException(status_code=503, detail=f"ThingSpeak error: HTTP {response.status_code}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="ThingSpeak request timed out")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"ThingSpeak unreachable: {str(e)}")


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
