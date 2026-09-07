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
from app.services.websocket_manager import manager
from app.services.telemetry_buffer import append_node_telemetry
from app.services.aktuator import baca_aktuator
from app.services.field_decoder import (
    LAYOUT_DEFAULT,
    extract_channel_fields,
    get_actuator_field,
    has_valve,
    is_support_channel,
)
from app.services.alerting import evaluate_sensor_thresholds, mark_node_online

logger = logging.getLogger(__name__)

# In-memory accumulated latest data per node_id across multiple channels
node_latest_data: Dict[str, Dict[str, Any]] = {}
node_latest_actuators: Dict[str, Any] = {}

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

            layout = node.field_layout or LAYOUT_DEFAULT

            # Layout menentukan pembongkaran field5 kanal pendukung Node 1.
            # Field null dilewati, bukan dijadikan nol.
            extracted_data = {}
            channel_uuid_str = str(channel.id)
            for nama_field, nilai in extract_channel_fields(
                data, layout=layout, channel_label=channel.label
            ).items():
                extracted_data[f"{channel_uuid_str}_{nama_field}"] = nilai

            # Decode actuator bitmask if support channel
            if is_support_channel(channel.label):
                actuator_f = get_actuator_field(layout)
                actuator_val = data.get(actuator_f)
                if actuator_val is not None:
                    node_latest_actuators[node.node_id] = baca_aktuator(
                        actuator_val, punya_valve=has_valve(layout)
                    )

            aktuator = node_latest_actuators.get(node.node_id)
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
                "aktuator": aktuator,
                "created_at": created_at
            }

            if created_at and merged_data:
                append_node_telemetry(node.node_id, {"created_at": created_at, **merged_data})

            # Broadcast combined multi-channel data instantly to frontend WebSockets
            await manager.broadcast(node.node_id, payload)
            await manager.broadcast("dashboard", payload)

            sensors = await sensor_repo.list_by_node(db, node.id)
            await evaluate_sensor_thresholds(db, node, sensors, merged_data)

            await node_repo.update_last_seen(db, node)
            await mark_node_online(db, node)

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
