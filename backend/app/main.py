from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.api import (
    instances,
    vnc,
    trading,
    monitoring,
    auth,
    notifications,
    users,
    servers,
    billing,
    accounts,
    copytrading,
)
from app.models.database import Base
from app.core.database import engine
from app.services.ssh_service import init_ssh_service
from app.services.billing_service import init_billing_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    if settings.ENCRYPTION_KEY:
        init_ssh_service(settings.ENCRYPTION_KEY)
        logger.info("SSH service initialized")

    if settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET:
        init_billing_service(settings.STRIPE_SECRET_KEY, settings.STRIPE_WEBHOOK_SECRET)
        logger.info("Billing service initialized")

    yield
    logger.info("Shutting down...")


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(instances.router, prefix="/api/v1/instances", tags=["Instances"])
app.include_router(vnc.router, prefix="/api/v1/vnc", tags=["VNC"])
app.include_router(trading.router, prefix="/api/v1/trading", tags=["Trading"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])
app.include_router(
    notifications.router, prefix="/api/v1/notifications", tags=["Notifications"]
)
app.include_router(servers.router, prefix="/api/v1/servers", tags=["Servers"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["Billing"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["MT5 Accounts"])
app.include_router(copytrading.router, prefix="/api/v1/copy", tags=["Copy Trading"])


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/api/v1/info")
async def info():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "mt5_image": settings.MT5_IMAGE,
        "features": [
            "instances",
            "vnc",
            "trading",
            "monitoring",
            "notifications",
            "accounts",
        ],
    }
