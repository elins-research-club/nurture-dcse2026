import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class ThingspeakChannel(Base):
    __tablename__ = "thingspeak_channels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.id"), nullable=False)
    channel_id = Column(String, nullable=False)
    read_api_key = Column(String, nullable=False)
    write_api_key = Column(String, nullable=False)
    label = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    node = relationship("Node", back_populates="channels")
