from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "G-Connect API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # ThingSpeak Polling
    THINGSPEAK_POLL_INTERVAL: int = 15
    OFFLINE_THRESHOLD_MINUTES: int = 15
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    THINGSPEAK_BASE_URL: str = "https://api.thingspeak.com"
    
    # Security
    SECRET_KEY: str = "change-this-in-production-long-secret-key-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/gconnect"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
