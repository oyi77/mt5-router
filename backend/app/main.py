from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.api import instances, vnc, trading, monitoring, auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
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
app.include_router(instances.router, prefix="/api/v1/instances", tags=["Instances"])
app.include_router(vnc.router, prefix="/api/v1/vnc", tags=["VNC"])
app.include_router(trading.router, prefix="/api/v1/trading", tags=["Trading"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/api/v1/info")
async def info():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "mt5_image": settings.MT5_IMAGE,
        "features": ["instances", "vnc", "trading", "monitoring"],
    }
