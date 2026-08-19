from sqlalchemy import Column, Integer
from app.core.database import Base

class SystemConfig(Base):
    __tablename__ = "system_configs"
    
    id = Column(Integer, primary_key=True, default=1)
    polling_interval = Column(Integer, default=15, nullable=False)
    data_retention_days = Column(Integer, default=30, nullable=False)
    offline_threshold_mins = Column(Integer, default=15, nullable=False)
