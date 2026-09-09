import asyncio
import json
import os
import uuid
from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.node import Node
from app.models.thingspeak_channel import ThingspeakChannel
from app.models.sensor import Sensor
from app.models.system_config import SystemConfig
from app.core.security import hash_password
from app.repositories import user_repo

ADMIN_USERNAME = "gconnect"
ADMIN_EMAIL = "gconnect@elins.ugm.ac.id"
ADMIN_PASSWORD = "atminelins123"

async def seed_all():
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 1. Seed Admin User
    async with AsyncSessionLocal() as db:
        admin_user = await user_repo.get_by_username(db, ADMIN_USERNAME)
        if not admin_user:
            await user_repo.create(
                db=db,
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
            )
            print(f"[OK] Created admin user: {ADMIN_USERNAME}")
        else:
            print(f"[SKIP] Admin user already exists: {ADMIN_USERNAME}")

    # 2. Seed Nodes, Channels, Sensors, Config from JSON
    json_path = os.path.join(os.path.dirname(__file__), "seed_data.json")
    if not os.path.exists(json_path):
        print(f"[WARN] No seed_data.json found at {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    async with AsyncSessionLocal() as db:
        # Nodes
        for n_data in data.get("nodes", []):
            existing = (await db.execute(select(Node).where(Node.node_id == n_data["node_id"]))).scalar_one_or_none()
            if not existing:
                node = Node(
                    id=uuid.UUID(n_data["id"]),
                    node_id=n_data["node_id"],
                    name=n_data["name"],
                    location=n_data.get("location"),
                    field_layout=n_data.get("field_layout", "node2_plain"),
                    latitude=n_data.get("latitude"),
                    longitude=n_data.get("longitude"),
                    is_active=n_data.get("is_active", True)
                )
                db.add(node)
                print(f"[OK] Added node: {node.node_id} ({node.name})")

        await db.commit()

        # Channels
        for c_data in data.get("channels", []):
            existing = (await db.execute(select(ThingspeakChannel).where(ThingspeakChannel.id == uuid.UUID(c_data["id"])))).scalar_one_or_none()
            if not existing:
                channel = ThingspeakChannel(
                    id=uuid.UUID(c_data["id"]),
                    node_id=uuid.UUID(c_data["node_id"]),
                    channel_id=c_data["channel_id"],
                    read_api_key=c_data["read_api_key"],
                    write_api_key=c_data["write_api_key"],
                    label=c_data.get("label")
                )
                db.add(channel)
                print(f"[OK] Added channel: {channel.channel_id} ({channel.label})")

        await db.commit()

        # Sensors
        for s_data in data.get("sensors", []):
            existing = (await db.execute(select(Sensor).where(Sensor.id == uuid.UUID(s_data["id"])))).scalar_one_or_none()
            if not existing:
                sensor = Sensor(
                    id=uuid.UUID(s_data["id"]),
                    node_id=uuid.UUID(s_data["node_id"]),
                    channel_id=uuid.UUID(s_data["channel_id"]) if s_data.get("channel_id") else None,
                    name=s_data["name"],
                    type=s_data["type"],
                    unit=s_data["unit"],
                    thingspeak_field=s_data["thingspeak_field"],
                    min_threshold=s_data.get("min_threshold"),
                    max_threshold=s_data.get("max_threshold"),
                    enabled=s_data.get("enabled", True)
                )
                db.add(sensor)

        await db.commit()
        print(f"[OK] Seeded {len(data.get('sensors', []))} sensors")

        # System Config
        for cfg_data in data.get("system_config", []):
            existing = (await db.execute(select(SystemConfig).where(SystemConfig.id == cfg_data["id"]))).scalar_one_or_none()
            if not existing:
                cfg = SystemConfig(
                    id=cfg_data["id"],
                    offline_threshold_mins=cfg_data.get("offline_threshold_mins", 15),
                    telegram_bot_token=cfg_data.get("telegram_bot_token"),
                    telegram_chat_id=cfg_data.get("telegram_chat_id")
                )
                db.add(cfg)
                print("[OK] Added system configuration")

        await db.commit()

    print("[SUCCESS] All initial database data seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_all())
