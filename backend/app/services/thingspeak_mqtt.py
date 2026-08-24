import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
from paho.mqtt.enums import MQTTProtocolVersion

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.repositories import node_repo, channel_repo, sensor_repo
from app.repositories.event_log_repo import event_log_repo
from app.schemas.event_log import EventLogCreate
from app.services.websocket_manager import manager
from app.services.telegram_service import send_telegram_alert

logger = logging.getLogger(__name__)

# In-memory accumulated latest data per node_id across multiple channels
node_latest_data: Dict[str, Dict[str, Any]] = {}
node_online_state: Dict[str, bool] = {}
sensor_alert_state: Dict[str, bool] = {}

_main_loop: Optional[asyncio.AbstractEventLoop] = None
_mqtt_client: Optional[mqtt.Client] = None


async def process_thingspeak_payload(channel_str_id: str, data: Dict[str, Any]):
    """Process a single channel payload received via ThingSpeak MQTT push and broadcast to WebSockets."""
    try:
        async with AsyncSessionLocal() as db:
            channel = await channel_repo.get_by_channel_id(db, channel_str_id)
            if not channel:
                logger.debug(f"[MQTT] Channel {channel_str_id} not mapped in DB. Skipping.")
                return

            node = await node_repo.get_by_id(db, channel.node_id)
            if not node or not node.is_active:
                return

            # Extract fields and prefix with channel UUID
            extracted_data = {}
            channel_uuid_str = str(channel.id)

            for i in range(1, 9):
                field_name = f"field{i}"
                if field_name in data and data[field_name] is not None:
                    val = data[field_name]
                    try:
                        extracted_data[f"{channel_uuid_str}_{field_name}"] = float(val)
                    except (ValueError, TypeError):
                        extracted_data[f"{channel_uuid_str}_{field_name}"] = val

            created_at = data.get("created_at") or datetime.now(timezone.utc).isoformat()

            # Merge with accumulated live state for this node (Dual-Channel Forward-Fill)
            if node.node_id not in node_latest_data:
                node_latest_data[node.node_id] = {}
            node_latest_data[node.node_id].update(extracted_data)

            merged_data = dict(node_latest_data[node.node_id])

            payload = {
                "event": "sensor_update",
                "node_id": node.node_id,
                "status": "online",
                "data": merged_data,
                "created_at": created_at
            }

            # Broadcast combined multi-channel data instantly to frontend WebSockets
            await manager.broadcast(node.node_id, payload)
            await manager.broadcast("dashboard", payload)

            # Check sensor threshold alerts
            sensors = await sensor_repo.list_by_node(db, node.id)
            for s in sensors:
                if not s.enabled:
                    continue

                key = f"{str(s.channel_id)}_{s.thingspeak_field}"
                val = merged_data.get(key)
                if val is not None and isinstance(val, (int, float)):
                    sensor_id_str = str(s.id)
                    currently_alerting = sensor_alert_state.get(sensor_id_str, False)

                    is_high = s.max_threshold is not None and val > s.max_threshold
                    is_low = s.min_threshold is not None and val < s.min_threshold

                    if (is_high or is_low) and not currently_alerting:
                        alert_type = 'High' if is_high else 'Low'
                        limit = s.max_threshold if is_high else s.min_threshold
                        msg = f"⚠️ <b>Threshold Alert</b>\nNode <code>{node.name}</code>\nSensor <b>{s.name}</b> is {alert_type}: {val}{s.unit} (Limit: {limit}{s.unit})"
                        await send_telegram_alert(db, msg)
                        await event_log_repo.create(db, EventLogCreate(level="WARNING", message=f"{s.name} is {alert_type}: {val}{s.unit}", node_id=node.id))
                        sensor_alert_state[sensor_id_str] = True

                    elif not (is_high or is_low) and currently_alerting:
                        msg = f"✅ <b>Threshold Recovered</b>\nNode <code>{node.name}</code>\nSensor <b>{s.name}</b> returned to normal: {val}{s.unit}"
                        await send_telegram_alert(db, msg)
                        await event_log_repo.create(db, EventLogCreate(level="INFO", message=f"{s.name} returned to normal: {val}{s.unit}", node_id=node.id))
                        sensor_alert_state[sensor_id_str] = False

            # Update last_seen in DB
            await node_repo.update_last_seen(db, node)

            # Check online transition
            was_online = node_online_state.get(node.node_id, True)
            if not was_online:
                msg = f"🟢 <b>Node Online</b>\nNode <code>{node.name}</code> ({node.node_id}) is back online!"
                await send_telegram_alert(db, msg)
                await event_log_repo.create(db, EventLogCreate(level="INFO", message=f"Node {node.name} is back online.", node_id=node.id))

            node_online_state[node.node_id] = True
            logger.info(f"[MQTT] Processed live data for node {node.node_id} (channel {channel_str_id}) -> {len(merged_data)} combined fields")

    except Exception as e:
        logger.error(f"[MQTT] Error processing payload for channel {channel_str_id}: {e}", exc_info=True)


def _on_mqtt_connect(client, userdata, flags, reason_code, properties=None):
    if not reason_code.is_failure:
        logger.info(f"[MQTT] Connected to ThingSpeak MQTT Broker ({settings.THINGSPEAK_MQTT_BROKER}:{settings.THINGSPEAK_MQTT_PORT}) successfully!")
        
        # Schedule subscription to active channels in the event loop
        if _main_loop and _main_loop.is_running():
            asyncio.run_coroutine_threadsafe(_subscribe_db_channels(client), _main_loop)
    else:
        logger.error(f"[MQTT] Connection failed with reason: {reason_code}")


async def _subscribe_db_channels(client: mqtt.Client):
    try:
        async with AsyncSessionLocal() as db:
            channels = await channel_repo.list_all(db)
            for c in channels:
                topic = f"channels/{c.channel_id}/subscribe"
                client.subscribe(topic)
                logger.info(f"[MQTT] Subscribed to topic: {topic}")
    except Exception as e:
        logger.error(f"[MQTT] Failed to subscribe DB channels: {e}")


def _on_mqtt_message(client, userdata, message):
    try:
        topic_str = str(message.topic)
        payload_bytes = message.payload
        payload_str = payload_bytes.decode("utf-8", errors="ignore")

        parts = topic_str.split("/")
        if len(parts) >= 2 and parts[0] == "channels":
            channel_id = parts[1]
            data = json.loads(payload_str)

            if _main_loop and _main_loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    process_thingspeak_payload(channel_id, data),
                    _main_loop
                )
    except Exception as e:
        logger.error(f"[MQTT] Error in on_message callback: {e}", exc_info=True)


async def mqtt_listener_loop():
    """Initializes and runs the MQTT client loop."""
    global _main_loop, _mqtt_client
    _main_loop = asyncio.get_running_loop()

    if not settings.THINGSPEAK_MQTT_CLIENT_ID or not settings.THINGSPEAK_MQTT_USERNAME:
        logger.warning("[MQTT] ThingSpeak MQTT credentials not configured. MQTT listener disabled.")
        return

    logger.info(f"[MQTT] Initializing MQTT client with Client ID: {settings.THINGSPEAK_MQTT_CLIENT_ID[:6]}***")

    _mqtt_client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=settings.THINGSPEAK_MQTT_CLIENT_ID,
        protocol=MQTTProtocolVersion.MQTTv311
    )
    _mqtt_client.username_pw_set(
        settings.THINGSPEAK_MQTT_USERNAME,
        settings.THINGSPEAK_MQTT_PASSWORD
    )
    _mqtt_client.on_connect = _on_mqtt_connect
    _mqtt_client.on_message = _on_mqtt_message

    try:
        _mqtt_client.connect(settings.THINGSPEAK_MQTT_BROKER, settings.THINGSPEAK_MQTT_PORT, keepalive=60)
        _mqtt_client.loop_start()
        logger.info("[MQTT] Background MQTT network loop started.")
    except Exception as e:
        logger.error(f"[MQTT] Failed to start MQTT client: {e}", exc_info=True)
