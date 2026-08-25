from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "G-Connect API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # ThingSpeak Polling & MQTT
    THINGSPEAK_POLL_INTERVAL: int = 15
    OFFLINE_THRESHOLD_MINUTES: int = 15
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    THINGSPEAK_BASE_URL: str = "https://api.thingspeak.com"
    
    # ThingSpeak MQTT
    THINGSPEAK_MQTT_BROKER: str = "mqtt3.thingspeak.com"
    THINGSPEAK_MQTT_PORT: int = 1883
    THINGSPEAK_MQTT_CLIENT_ID: Optional[str] = None
    THINGSPEAK_MQTT_USERNAME: Optional[str] = None
    THINGSPEAK_MQTT_PASSWORD: Optional[str] = None
    
    # Web Push (VAPID). Kunci publik ikut dikirim ke browser supaya bisa
    # mendaftar langganan; kunci privat jangan pernah keluar dari server.
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_SUBJECT: str = "mailto:admin@example.com"

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

    @property
    def WEBPUSH_ENABLED(self) -> bool:
        return bool(self.VAPID_PUBLIC_KEY and self.VAPID_PRIVATE_KEY)

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
