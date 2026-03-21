from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "MT5 Router"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    JWT_SECRET: str = "mt5-router-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    DOCKER_SOCKET: str = "unix://var/run/docker.sock"
    MT5_IMAGE: str = "lprett/mt5linux:mt5-installed"
    MT5_NETWORK: str = "bridge"
    MT5_RPYC_PORT: int = 18812
    MT5_VNC_PORT: int = 6081
    DATABASE_URL: str = "sqlite:///./data/mt5router.db"
    METRICS_INTERVAL: int = 10
    ALERT_COOLDOWN: int = 300

    class Config:
        env_file = ".env"


settings = Settings()
