import asyncio
import logging
import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.repositories import node_repo, channel_repo, sensor_repo
from app.services.websocket_manager import manager
from app.services.telegram_service import send_telegram_alert
from app.repositories.event_log_repo import event_log_repo
from app.schemas.event_log import EventLogCreate
from datetime import datetime, timezone
from sqlalchemy.future import select
from app.models.system_config import SystemConfig
from app.services.aktuator import baca_aktuator
from app.services.webpush_service import kirim_push
from app.services.telemetry_buffer import append_node_telemetry


from app.services.alert_formatter import (
    format_sensor_alert_telegram,
    format_sensor_recovered_telegram,
    format_sensor_push,
    format_sensor_recovered_push,
    format_node_offline_telegram,
    format_node_online_telegram,
    format_node_offline_push,
    format_node_online_push,
)

logger = logging.getLogger(__name__)

# Track online state in memory to prevent spamming alerts
# {node_id: is_online_bool}
node_online_state = {}

# Track sensor alert state
# {sensor_id: is_alerting_bool}
sensor_alert_state = {}


# Shared HTTP Client with Keep-Alive Connection Pool
_http_client: Optional[httpx.AsyncClient] = None

def get_http_client() -> httpx.AsyncClient:
    """Returns a shared httpx.AsyncClient with Keep-Alive connection pooling for ThingSpeak HTTP requests."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=50, keepalive_expiry=30.0)
        _http_client = httpx.AsyncClient(timeout=10.0, limits=limits)
    return _http_client

async def close_http_client():
    """Closes the shared HTTP client connection pool gracefully."""
    global _http_client
    if _http_client is not None and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None


async def fetch_latest(channel_id: str, read_api_key: str, client: Optional[httpx.AsyncClient] = None) -> Optional[Dict[str, Any]]:
    url = f"{settings.THINGSPEAK_BASE_URL}/channels/{channel_id}/feeds/last.json"
    params = {"api_key": read_api_key}
    http_client = client or get_http_client()
    
    try:
        response = await http_client.get(url, params=params)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            logger.warning(f"ThingSpeak rate limited for channel {channel_id}")
            return None
        else:
            logger.warning(f"ThingSpeak error for channel {channel_id}: HTTP {response.status_code}")
            return None
            
    except httpx.TimeoutException:
        logger.warning(f"ThingSpeak timeout for channel {channel_id}")
        return None
    except httpx.RequestError as e:
        logger.warning(f"ThingSpeak request error for channel {channel_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching from ThingSpeak for channel {channel_id}: {e}")
        return None

async def poll_node(node_id: str, channels: list, db_session):
    if not channels:
        return

    # Fetch all channels in parallel using shared HTTP connection pool
    http_client = get_http_client()
    tasks = [fetch_latest(c.channel_id, c.read_api_key, client=http_client) for c in channels]
    results = await asyncio.gather(*tasks)
    
    # If all channels return None, consider the node offline
    if all(r is None for r in results):
        payload = {"event": "node_status", "node_id": node_id, "status": "offline"}
        await manager.broadcast(node_id, payload)
        await manager.broadcast("dashboard", payload)
        return

    extracted_data = {}
    latest_ts = None
    aktuator = None

    
    for channel, data in zip(channels, results):
        if data is None:
            continue

       
        # Parse fields and prefix with the channel's UUID
        channel_uuid_str = str(channel.id)
        for i in range(1, 9):
            field_name = f"field{i}"
            if field_name in data and data[field_name] is not None:
                try:
                    extracted_data[f"{channel_uuid_str}_{field_name}"] = float(data[field_name])
                except ValueError:
                    extracted_data[f"{channel_uuid_str}_{field_name}"] = data[field_name]
         # field8 kanal pendukung itu bitmask, bukan pengukuran -- didekode
                # terpisah supaya tidak ikut dibandingkan dengan ambang.
            if (channel.label or "").strip().lower() == "pendukung":
                aktuator = baca_aktuator(data.get("field8"))
                  
        # Find the most recent timestamp among all channels
        ts = data.get("created_at")
        if ts:
            if latest_ts is None or ts > latest_ts:
                latest_ts = ts
                
    payload = {
        "event": "sensor_update",
        "node_id": node_id,
        "status": "online",
        "data": extracted_data,
        "aktuator": aktuator,
        "created_at": latest_ts
    }

    if latest_ts and extracted_data:
        append_node_telemetry(node_id, {"created_at": latest_ts, **extracted_data})

    await manager.broadcast(node_id, payload)
    await manager.broadcast("dashboard", payload)
    

    node = await node_repo.get_by_node_id(db_session, node_id)
    if node:
        # Check thresholds
        sensors = await sensor_repo.list_by_node(db_session, node.id)
        for s in sensors:
            if not s.enabled:
                continue
                
            key = f"{str(s.channel_id)}_{s.thingspeak_field}"
            val = extracted_data.get(key)
            if val is not None and isinstance(val, (int, float)):
                sensor_id_str = str(s.id)
                currently_alerting = sensor_alert_state.get(sensor_id_str, False)
                
                is_high = s.max_threshold is not None and val > s.max_threshold
                is_low = s.min_threshold is not None and val < s.min_threshold
                
                if (is_high or is_low) and not currently_alerting:
                    # Trigger alert
                    msg = format_sensor_alert_telegram(
                        node_name=node.name,
                        sensor_name=s.name,
                        val=val,
                        unit=s.unit or "",
                        is_high=is_high,
                        min_thresh=s.min_threshold,
                        max_thresh=s.max_threshold
                    )
                    await send_telegram_alert(db_session, msg)
                    
                    push_judul, push_isi = format_sensor_push(
                        node_name=node.name,
                        sensor_name=s.name,
                        val=val,
                        unit=s.unit or "",
                        is_high=is_high,
                        min_thresh=s.min_threshold,
                        max_thresh=s.max_threshold
                    )
                    await kirim_push(db_session, push_judul, push_isi, "/dashboard")
                    
                    status_str = "Tinggi" if is_high else "Rendah"
                    await event_log_repo.create(db_session, EventLogCreate(level="WARNING", message=f"{s.name} ({status_str}): {val} {s.unit or ''}", node_id=node.id))
                    sensor_alert_state[sensor_id_str] = True
                
                elif not (is_high or is_low) and currently_alerting:
                    # Sensor kembali normal - reset state tanpa kirim spam notifikasi
                    await event_log_repo.create(db_session, EventLogCreate(level="INFO", message=f"{s.name} kembali normal: {val} {s.unit or ''}", node_id=node.id))
                    sensor_alert_state[sensor_id_str] = False

        await node_repo.update_last_seen(db_session, node)

        # Check if it was previously offline and just came back online
        was_online = node_online_state.get(node_id, True)
        if not was_online:
            msg = format_node_online_telegram(node_name=node.name, node_id=node_id)
            await send_telegram_alert(db_session, msg)
            
            p_judul, p_isi = format_node_online_push(node_name=node.name)
            await kirim_push(db_session, p_judul, p_isi, "/dashboard")
            
            await event_log_repo.create(db_session, EventLogCreate(level="INFO", message=f"Node {node.name} kembali online.", node_id=node.id))
        
        node_online_state[node_id] = True

async def check_offline_nodes(db_session):
    nodes = await node_repo.list_all(db_session)
    active_nodes = [n for n in nodes if n.is_active]
    now = datetime.utcnow()
    
    # Read dynamic offline threshold from database
    result = await db_session.execute(select(SystemConfig).filter_by(id=1))
    config = result.scalars().first()
    offline_thresh_mins = config.offline_threshold_mins if (config and config.offline_threshold_mins) else settings.OFFLINE_THRESHOLD_MINUTES
    
    for node in active_nodes:
        if node.last_seen:
            diff_minutes = (now - node.last_seen).total_seconds() / 60.0
            is_currently_online = node_online_state.get(node.node_id, True)
            
            if diff_minutes > offline_thresh_mins and is_currently_online:
                msg = format_node_offline_telegram(node_name=node.name, node_id=node.node_id, minutes=int(diff_minutes))
                await send_telegram_alert(db_session, msg)
                
                p_judul, p_isi = format_node_offline_push(node_name=node.name, minutes=int(diff_minutes))
                await kirim_push(db_session, p_judul, p_isi, "/dashboard")
                
                await event_log_repo.create(db_session, EventLogCreate(level="ERROR", message=f"Node {node.name} offline (> {int(diff_minutes)} menit tanpa data).", node_id=node.id))
                node_online_state[node.node_id] = False

async def polling_loop(app):
    if settings.THINGSPEAK_MQTT_CLIENT_ID and settings.THINGSPEAK_MQTT_USERNAME:
        logger.info("[Poller] MQTT enabled. Poller will run as watchdog for offline nodes every 60s.")
        while True:
            try:
                async with AsyncSessionLocal() as db_session:
                    await check_offline_nodes(db_session)
            except Exception as e:
                logger.error(f"[Poller Watchdog] Error checking offline nodes: {e}")
            await asyncio.sleep(60)
    else:
        logger.info("[Poller] Starting ThingSpeak HTTP polling fallback loop...")
        while True:
            try:
                async with AsyncSessionLocal() as db_session:
                    nodes = await node_repo.list_all(db_session)
                    active_nodes = [n for n in nodes if n.is_active]
                    
                    for node in active_nodes:
                        channels = await channel_repo.get_by_node_id(db_session, node.id)
                        if channels:
                            await poll_node(node.node_id, channels, db_session)
                            
                    await check_offline_nodes(db_session)
                            
            except Exception as e:
                logger.error(f"Error in polling loop iteration: {e}")
                
            await asyncio.sleep(settings.THINGSPEAK_POLL_INTERVAL)
