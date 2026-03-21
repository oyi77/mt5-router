from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import asyncio
import docker
import psutil
import logging
from datetime import datetime

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


@router.get("/alerts")
async def get_alerts():
    return {"alerts": [], "count": 0}
