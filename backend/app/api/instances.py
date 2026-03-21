from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import docker
import asyncio
import json
import logging
import os

from app.auth.jwt import get_current_user
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def get_docker_client():
    return docker.from_env()


def get_instance_info(container):
    container.reload()
    ports = container.ports
    return {
        "id": container.id[:12],
        "name": container.name,
        "status": container.status,
        "image": container.image.tags[0] if container.image.tags else "unknown",
        "created": container.attrs["Created"],
        "rpyc_port": ports.get("18812/tcp", [{}])[0].get("HostPort")
        if ports.get("18812/tcp")
        else None,
        "vnc_port": ports.get("6081/tcp", [{}])[0].get("HostPort")
        if ports.get("6081/tcp")
        else None,
        "labels": container.labels,
    }


@router.get("")
async def list_instances(user: dict = Depends(get_current_user)):
    client = get_docker_client()
    containers = client.containers.list(
        all=True, filters={"label": "mt5-router.instance"}
    )
    return [get_instance_info(c) for c in containers]


@router.get("/{instance_id}")
async def get_instance(instance_id: str, user: dict = Depends(get_current_user)):
    client = get_docker_client()
    try:
        container = client.containers.get(instance_id)
        return get_instance_info(container)
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Instance not found")


@router.post("")
async def create_instance(user: dict = Depends(get_current_user)):
    client = get_docker_client()
    instance_name = f"mt5-{os.urandom(4).hex()}"

    try:
        container = client.containers.run(
            settings.MT5_IMAGE,
            name=instance_name,
            detach=True,
            ports={"18812/tcp": None, "6081/tcp": None},
            labels={"mt5-router.instance": "true", "mt5-router.created": "auto"},
            shm_size="2gb",
            cap_add=["SYS_ADMIN"],
            restart_policy={"Name": "unless-stopped"},
        )
        return get_instance_info(container)
    except Exception as e:
        logger.error(f"Failed to create instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{instance_id}/start")
async def start_instance(instance_id: str, user: dict = Depends(get_current_user)):
    client = get_docker_client()
    try:
        container = client.containers.get(instance_id)
        container.start()
        return {"status": "started", "instance_id": instance_id}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Instance not found")


@router.post("/{instance_id}/stop")
async def stop_instance(instance_id: str, user: dict = Depends(get_current_user)):
    client = get_docker_client()
    try:
        container = client.containers.get(instance_id)
        container.stop(timeout=30)
        return {"status": "stopped", "instance_id": instance_id}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Instance not found")


@router.post("/{instance_id}/restart")
async def restart_instance(instance_id: str, user: dict = Depends(get_current_user)):
    client = get_docker_client()
    try:
        container = client.containers.get(instance_id)
        container.restart(timeout=30)
        return {"status": "restarted", "instance_id": instance_id}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Instance not found")


@router.delete("/{instance_id}")
async def delete_instance(instance_id: str, user: dict = Depends(get_current_user)):
    client = get_docker_client()
    try:
        container = client.containers.get(instance_id)
        container.remove(force=True)
        return {"status": "deleted", "instance_id": instance_id}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Instance not found")


@router.get("/{instance_id}/logs")
async def get_instance_logs(
    instance_id: str, lines: int = 100, user: dict = Depends(get_current_user)
):
    client = get_docker_client()
    try:
        container = client.containers.get(instance_id)
        logs = container.logs(tail=lines).decode("utf-8", errors="replace")
        return {"logs": logs.split("\n")}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Instance not found")


@router.get("/{instance_id}/stats")
async def get_instance_stats(instance_id: str, user: dict = Depends(get_current_user)):
    client = get_docker_client()
    try:
        container = client.containers.get(instance_id)
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
        memory_percent = (
            (memory_usage / memory_limit * 100.0) if memory_limit > 0 else 0
        )

        return {
            "cpu_percent": round(cpu_percent, 2),
            "memory_usage_mb": round(memory_usage / 1024 / 1024, 2),
            "memory_limit_mb": round(memory_limit / 1024 / 1024, 2),
            "memory_percent": round(memory_percent, 2),
            "network_rx": stats.get("networks", {}).get("eth0", {}).get("rx_bytes", 0),
            "network_tx": stats.get("networks", {}).get("eth0", {}).get("tx_bytes", 0),
        }
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Instance not found")
