from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
import os

from app.config import settings
from app.api import (
    admin,
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
    statistics,
    webhooks,
)
from app.models.database import Base
from app.core.database import engine
from app.services.ssh_service import init_ssh_service
from app.services.billing_service import init_billing_service
from app.services.nowpayments_service import init_nowpayments_service
from app.services.metrics_collector import (
    start_metrics_collector,
    stop_metrics_collector,
)

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

    if settings.NOWPAYMENTS_API_KEY:
        init_nowpayments_service(
            settings.NOWPAYMENTS_API_KEY,
            settings.NOWPAYMENTS_IPN_SECRET,
            settings.NOWPAYMENTS_SANDBOX,
        )
        logger.info("NOWPayments service initialized")

    start_metrics_collector(interval=60)
    logger.info("Metrics collector started")

    yield
    stop_metrics_collector()
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
app.include_router(
    statistics.router, prefix="/api/v1/stats", tags=["Trading Statistics"]
)
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["Webhooks"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])


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


FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist"
)

if os.path.exists(FRONTEND_DIR):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")),
        name="assets",
    )

    @app.get("/vite.svg")
    async def serve_vite_svg():
        svg_path = os.path.join(FRONTEND_DIR, "vite.svg")
        if os.path.exists(svg_path):
            return FileResponse(svg_path)
        return {"detail": "Not Found"}

    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        if (
            full_path.startswith("api/")
            or full_path.startswith("docs")
            or full_path.startswith("redoc")
            or full_path.startswith("openapi")
        ):
            return {"detail": "Not Found"}

        file_path = os.path.join(FRONTEND_DIR, full_path)
        if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)

        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    logger.info(f"Frontend static files mounted from {FRONTEND_DIR}")
else:
    logger.warning(f"Frontend directory not found at {FRONTEND_DIR}")
