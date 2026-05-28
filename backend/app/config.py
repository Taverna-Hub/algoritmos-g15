from pathlib import Path

from pydantic_settings import BaseSettings
from functools import lru_cache

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5433/wifi_detection"
    
    # MQTT
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    mqtt_subscribe_topic: str = "nodered/wifi/data"
    mqtt_username: str = ""
    mqtt_password: str = ""
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # ML Service
    ml_service_url: str = "http://localhost:8001"
    ml_cache_ttl: int = 300
    
    class Config:
        env_file = ENV_FILE
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
