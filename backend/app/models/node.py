import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    node_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Menentukan cara field ThingSpeak dibongkar. Node 1 memampatkan dua arus ke
    # field5 kanal pendukung dan punya valve; Node 2 tidak. Lihat
    # services/field_decoder.py. Default "node2_plain" karena itu yang tidak
    # mengubah apa pun kalau kolom ini belum diisi.
    field_layout: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="node2_plain", default="node2_plain"
    )
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    channels = relationship("ThingspeakChannel", back_populates="node", cascade="all, delete-orphan")
    sensors = relationship("Sensor", back_populates="node", cascade="all, delete-orphan")
    actuators = relationship("Actuator", back_populates="node", cascade="all, delete-orphan")
    event_logs = relationship("EventLog", back_populates="node", cascade="all, delete-orphan")
