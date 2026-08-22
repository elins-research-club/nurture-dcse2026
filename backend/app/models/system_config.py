from sqlalchemy import Column, Integer, String
from app.core.database import Base

class SystemConfig(Base):
    __tablename__ = "system_configs"
    
    id = Column(Integer, primary_key=True, default=1)
    node_status_check_interval = Column(Integer, default=15, nullable=False)
    telemetry_cache_interval = Column(Integer, default=30, nullable=False)
    data_retention_days = Column(Integer, default=30, nullable=False)
    offline_threshold_mins = Column(Integer, default=15, nullable=False)
    telegram_bot_token = Column(String, nullable=True)
    telegram_chat_id = Column(String, nullable=True)
