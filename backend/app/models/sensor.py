import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.id"), nullable=False)
    channel_id = Column(UUID(as_uuid=True), ForeignKey("thingspeak_channels.id"), nullable=True)
    type = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    unit = Column(String(20), nullable=False)
    thingspeak_field = Column(String(10), nullable=False)
    min_threshold = Column(Float, nullable=True)
    max_threshold = Column(Float, nullable=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    node = relationship("Node", back_populates="sensors")
    channel = relationship("ThingspeakChannel")
