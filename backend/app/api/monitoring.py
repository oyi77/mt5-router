from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session
import asyncio
import docker
import psutil
import logging
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.database import ServerMetrics, InstanceMetrics

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/system")
async def get_system_metrics():
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent,
            "used": psutil.virtual_memory().used,
        },
        "disk": {
            "total": psutil.disk_usage("/").total,
            "used": psutil.disk_usage("/").used,
            "free": psutil.disk_usage("/").free,
            "percent": psutil.disk_usage("/").percent,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/instances")
async def get_instances_metrics():
    client = docker.from_env()
    containers = client.containers.list(
        all=True, filters={"label": "mt5-router.instance"}
    )

    metrics = []
    for container in containers:
        try:
            stats = container.stats(stream=False)

            cpu_delta = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )
            system_delta = (
                stats["cpu_stats"]["system_cpu_usage"]
                - stats["precpu_stats"]["system_cpu_usage"]
            )
            cpu_percent = (cpu_delta / system_delta * 100.0) if system_delta > 0 else 0

            memory_usage = stats["memory_stats"].get("usage", 0)
            memory_limit = stats["memory_stats"].get("limit", 1)

            metrics.append(
                {
                    "id": container.id[:12],
                    "name": container.name,
                    "status": container.status,
                    "cpu_percent": round(cpu_percent, 2),
                    "memory_usage_mb": round(memory_usage / 1024 / 1024, 2),
                    "memory_limit_mb": round(memory_limit / 1024 / 1024, 2),
                    "memory_percent": round((memory_usage / memory_limit * 100.0), 2)
                    if memory_limit > 0
                    else 0,
                }
            )
        except Exception as e:
            logger.error(f"Error getting stats for {container.name}: {e}")

    return metrics


@router.websocket("/stream")
async def metrics_stream(websocket: WebSocket):
    await websocket.accept()

    client = docker.from_env()

    try:
        while True:
            system = {
                "cpu": psutil.cpu_percent(interval=1),
                "memory": psutil.virtual_memory().percent,
                "disk": psutil.disk_usage("/").percent,
            }

            containers = client.containers.list(
                filters={"label": "mt5-router.instance"}
            )
            instances = []
            for c in containers:
                try:
                    stats = c.stats(stream=False)
                    cpu_delta = (
                        stats["cpu_stats"]["cpu_usage"]["total_usage"]
                        - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                    )
                    system_delta = (
                        stats["cpu_stats"]["system_cpu_usage"]
                        - stats["precpu_stats"]["system_cpu_usage"]
                    )
                    cpu_percent = (
                        (cpu_delta / system_delta * 100.0) if system_delta > 0 else 0
                    )
                    instances.append(
                        {
                            "id": c.id[:12],
                            "name": c.name,
                            "status": c.status,
                            "cpu": round(cpu_percent, 2),
                            "memory": round(
                                stats["memory_stats"].get("usage", 0)
                                / stats["memory_stats"].get("limit", 1)
                                * 100,
                                2,
                            ),
                        }
                    )
                except:
                    pass

            await websocket.send_json(
                {
                    "type": "metrics",
                    "system": system,
                    "instances": instances,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            await asyncio.sleep(5)
    except WebSocketDisconnect:
        logger.info("Metrics stream disconnected")
    except Exception as e:
        logger.error(f"Metrics stream error: {e}")


@router.get("/servers/{server_id}/metrics")
async def get_server_metrics_history(
    server_id: int,
    hours: int = Query(default=24, ge=1, le=720),
    db: Session = Depends(get_db),
):
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    records = (
        db.query(ServerMetrics)
        .filter(ServerMetrics.server_id == server_id)
        .filter(ServerMetrics.recorded_at >= cutoff)
        .order_by(ServerMetrics.recorded_at)
        .all()
    )
    return [
        {
            "id": r.id,
            "server_id": r.server_id,
            "cpu_percent": r.cpu_percent,
            "memory_total_mb": r.memory_total_mb,
            "memory_used_mb": r.memory_used_mb,
            "disk_total_gb": r.disk_total_gb,
            "disk_used_gb": r.disk_used_gb,
            "network_rx_mb": r.network_rx_mb,
            "network_tx_mb": r.network_tx_mb,
            "docker_containers_total": r.docker_containers_total,
            "docker_containers_running": r.docker_containers_running,
            "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
        }
        for r in records
    ]


@router.get("/instances/{instance_id}/metrics")
async def get_instance_metrics_history(
    instance_id: str,
    hours: int = Query(default=24, ge=1, le=720),
    db: Session = Depends(get_db),
):
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    records = (
        db.query(InstanceMetrics)
        .filter(InstanceMetrics.instance_id == instance_id)
        .filter(InstanceMetrics.recorded_at >= cutoff)
        .order_by(InstanceMetrics.recorded_at)
        .all()
    )
    return [
        {
            "id": r.id,
            "instance_id": r.instance_id,
            "instance_name": r.instance_name,
            "cpu_percent": r.cpu_percent,
            "memory_usage_mb": r.memory_usage_mb,
            "memory_limit_mb": r.memory_limit_mb,
            "memory_percent": r.memory_percent,
            "network_rx_mb": r.network_rx_mb,
            "network_tx_mb": r.network_tx_mb,
            "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
        }
        for r in records
    ]


@router.get("/alerts")
async def get_alerts():
    return {"alerts": [], "count": 0}
