import asyncio
import logging
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.repositories import node_repo, channel_repo, sensor_repo
from app.services.websocket_manager import manager
from datetime import datetime
from sqlalchemy.future import select
from app.models.system_config import SystemConfig
from app.services.aktuator import baca_aktuator
from app.services.power_system import ekstrak_dan_hitung_daya
from app.services.telemetry_buffer import append_node_telemetry
from app.services.field_decoder import (
    LAYOUT_DEFAULT,
    extract_channel_fields,
    get_actuator_field,
    has_valve,
    is_support_channel,
)
from app.services.alerting import (
    evaluate_sensor_thresholds,
    mark_node_offline,
    mark_node_online,
    node_online_state,
)

logger = logging.getLogger(__name__)


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


async def poll_node(node_id: str, channels: list, db_session, layout: str = LAYOUT_DEFAULT):
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

    extracted_data: Dict[str, Any] = {}
    latest_ts = None
    aktuator = None

    for channel, data in zip(channels, results):
        if data is None:
            continue

        # Layout menentukan apakah field5 kanal pendukung dipampatkan (Node 1)
        # atau arus biasa (Node 2). Field null dilewati, tidak dijadikan nol.
        channel_uuid_str = str(channel.id)
        for nama_field, nilai in extract_channel_fields(
            data, layout=layout, channel_label=channel.label
        ).items():
            extracted_data[f"{channel_uuid_str}_{nama_field}"] = nilai

        # Bitmask aktuator kanal pendukung (field7 di Node 1, field8 di Node 2) didekode
        # terpisah supaya tidak ikut dibandingkan dengan ambang sensor.
        if is_support_channel(channel.label):
            field_aktuator = get_actuator_field(layout)
            aktuator = baca_aktuator(data.get(field_aktuator), punya_valve=has_valve(layout))

        # Find the most recent timestamp among all channels
        ts = data.get("created_at")
        if ts:
            if latest_ts is None or ts > latest_ts:
                latest_ts = ts

    node = await node_repo.get_by_node_id(db_session, node_id)
    power_metrics = None
    if node:
        sensors = await sensor_repo.list_by_node(db_session, node.id)
        power_metrics = ekstrak_dan_hitung_daya(sensors, extracted_data, node_id=node_id)
        await evaluate_sensor_thresholds(db_session, node, sensors, extracted_data)
        await node_repo.update_last_seen(db_session, node)
        await mark_node_online(db_session, node)

    payload = {
        "event": "sensor_update",
        "node_id": node_id,
        "status": "online",
        "data": extracted_data,
        "aktuator": aktuator,
        "power_metrics": power_metrics,
        "created_at": latest_ts
    }

    if latest_ts and extracted_data:
        append_node_telemetry(node_id, {"created_at": latest_ts, **extracted_data})

    await manager.broadcast(node_id, payload)
    await manager.broadcast("dashboard", payload)


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
            if diff_minutes > offline_thresh_mins:
                # mark_node_offline sendiri yang menjaga agar notifikasi cuma
                # dikirim sekali per transisi.
                await mark_node_offline(db_session, node, int(diff_minutes))


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
                            await poll_node(
                                node.node_id,
                                channels,
                                db_session,
                                layout=node.field_layout or LAYOUT_DEFAULT,
                            )

                    await check_offline_nodes(db_session)

            except Exception as e:
                logger.error(f"Error in polling loop iteration: {e}")

            await asyncio.sleep(settings.THINGSPEAK_POLL_INTERVAL)
