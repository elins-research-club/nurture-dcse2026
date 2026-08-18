import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.id"), nullable=True)
    level = Column(String(20), nullable=False, default="INFO") # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    node = relationship("Node", back_populates="event_logs")
