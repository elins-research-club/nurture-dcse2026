import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Actuator(Base):
    __tablename__ = "actuators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.id"), nullable=False)
    type = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    current_state = Column(String(10), default="OFF")
    controllable = Column(Boolean, default=True)
    enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    node = relationship("Node", back_populates="actuators")
