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
    API_KEY_PREFIX: str = "mtr_"
    RATE_LIMIT_PER_MINUTE: int = 100
    ENCRYPTION_KEY: str = "your-fernet-key-here"
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_BASIC_MONTHLY: str = ""
    STRIPE_PRICE_PRO_MONTHLY: str = ""

    # NOWPayments (crypto)
    NOWPAYMENTS_API_KEY: str = ""
    NOWPAYMENTS_IPN_SECRET: str = ""
    NOWPAYMENTS_SANDBOX: bool = True

    # Email (SMTP)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""
    BASE_URL: str = "https://mt-oc.aitradepulse.com"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # Database pooling
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    class Config:
        env_file = ".env"


settings = Settings()
