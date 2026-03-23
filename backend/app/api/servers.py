from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime
import random
import docker
import psutil
import platform

from app.core.database import get_db
from app.models.database import SSHServer, ServerMetrics, Instance
from app.auth.jwt import get_current_user
from app.services.ssh_service import ssh_service

router = APIRouter()


@router.get("/local/health")
async def local_server_health(user=Depends(get_current_user)):
    """Get health metrics for the local Docker server."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        client = docker.from_env()
        containers = client.containers.list(
            all=True, filters={"label": "mt5-router.instance"}
        )

        instances = []
        for c in containers:
            ports = c.ports
            instances.append(
                {
                    "id": c.id[:12],
                    "name": c.name,
                    "status": c.status,
                    "rpyc_port": ports.get("18812/tcp", [{}])[0].get("HostPort")
                    if ports.get("18812/tcp")
                    else None,
                    "vnc_port": ports.get("6081/tcp", [{}])[0].get("HostPort")
                    if ports.get("6081/tcp")
                    else None,
                }
            )

        return {
            "server_id": 0,
            "status": "healthy",
            "metrics": {
                "cpu_percent": round(cpu_percent, 1),
                "memory": {
                    "total": memory.total,
                    "used": memory.used,
                    "percent": round(memory.percent, 1),
                },
                "disk": {
                    "total": f"{disk.total / (1024**3):.1f}G",
                    "used": f"{disk.used / (1024**3):.1f}G",
                    "percent": round(disk.percent, 1),
                },
                "hostname": platform.node(),
                "containers_total": len(containers),
                "containers_running": sum(
                    1 for c in containers if c.status == "running"
                ),
            },
            "instances": instances,
            "checked_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get local server health: {e}"
        )


class ServerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    host: str = Field(..., min_length=1)
    port: int = Field(default=22, ge=1, le=65535)
    username: str = Field(..., min_length=1)
    private_key: Optional[str] = None
    password: Optional[str] = None
    use_key_auth: bool = True
    docker_socket: str = "/var/run/docker.sock"


class ServerUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    private_key: Optional[str] = None
    password: Optional[str] = None
    use_key_auth: Optional[bool] = None
    is_active: Optional[bool] = None


class ServerResponse(BaseModel):
    id: int
    name: str
    host: str
    port: int
    username: str
    use_key_auth: bool
    docker_socket: str
    is_active: bool
    health_status: str
    last_health_check: Optional[datetime]
    created_at: datetime


class ServerHealthResponse(BaseModel):
    server_id: int
    status: str
    metrics: Optional[dict] = None
    instances: Optional[List[dict]] = None
    checked_at: str


class InstanceCreate(BaseModel):
    name: Optional[str] = None
    image: str = "lprett/mt5linux:mt5-installed"


def get_ssh_connection(server: SSHServer, service):
    private_key = None
    password = None

    if server.use_key_auth and server.encrypted_private_key:
        private_key = service.decrypt_secret(server.encrypted_private_key)
    elif server.encrypted_password:
        password = service.decrypt_secret(server.encrypted_password)

    client = service.create_client(
        host=server.host,
        port=server.port,
        username=server.username,
        private_key=private_key,
        password=password,
    )

    if not client:
        raise HTTPException(
            status_code=500, detail=f"Failed to connect to {server.host}"
        )

    return client


@router.post("")
async def create_server(
    server_data: ServerCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not ssh_service:
        raise HTTPException(status_code=500, detail="SSH service not initialized")

    private_key_encrypted = None
    password_encrypted = None

    if server_data.use_key_auth:
        if not server_data.private_key:
            raise HTTPException(
                status_code=400, detail="Private key required for key authentication"
            )
        private_key_encrypted = ssh_service.encrypt_secret(server_data.private_key)
    else:
        if not server_data.password:
            raise HTTPException(
                status_code=400, detail="Password required for password authentication"
            )
        password_encrypted = ssh_service.encrypt_secret(server_data.password)

    test_client = ssh_service.create_client(
        host=server_data.host,
        port=server_data.port,
        username=server_data.username,
        private_key=server_data.private_key if server_data.use_key_auth else None,
        password=server_data.password if not server_data.use_key_auth else None,
        timeout=15,
    )

    if not test_client:
        raise HTTPException(
            status_code=400, detail="Cannot connect to server. Check credentials."
        )

    test_client.close()

    server = SSHServer(
        user_id=int(user["sub"]),
        name=server_data.name,
        host=server_data.host,
        port=server_data.port,
        username=server_data.username,
        encrypted_private_key=private_key_encrypted,
        encrypted_password=password_encrypted,
        use_key_auth=server_data.use_key_auth,
        docker_socket=server_data.docker_socket,
        health_status="unknown",
    )

    db.add(server)
    db.commit()
    db.refresh(server)

    return {
        "id": server.id,
        "name": server.name,
        "host": server.host,
        "port": server.port,
        "status": "created",
        "message": "Server added successfully. Run health check to verify connection.",
    }


@router.get("")
async def list_servers(user=Depends(get_current_user), db: Session = Depends(get_db)):
    servers = db.query(SSHServer).filter(SSHServer.user_id == int(user["sub"])).all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "host": s.host,
            "port": s.port,
            "username": s.username,
            "use_key_auth": s.use_key_auth,
            "is_active": s.is_active,
            "health_status": s.health_status,
            "last_health_check": s.last_health_check,
            "created_at": s.created_at,
        }
        for s in servers
    ]


@router.get("/{server_id}")
async def get_server(
    server_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)
):
    server = (
        db.query(SSHServer)
        .filter(SSHServer.id == server_id, SSHServer.user_id == int(user["sub"]))
        .first()
    )

    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    return {
        "id": server.id,
        "name": server.name,
        "host": server.host,
        "port": server.port,
        "username": server.username,
        "use_key_auth": server.use_key_auth,
        "docker_socket": server.docker_socket,
        "is_active": server.is_active,
        "health_status": server.health_status,
        "last_health_check": server.last_health_check,
        "created_at": server.created_at,
    }


@router.put("/{server_id}")
async def update_server(
    server_id: int,
    update: ServerUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    server = (
        db.query(SSHServer)
        .filter(SSHServer.id == server_id, SSHServer.user_id == int(user["sub"]))
        .first()
    )

    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if not ssh_service:
        raise HTTPException(status_code=500, detail="SSH service not initialized")

    if update.name is not None:
        server.name = update.name
    if update.host is not None:
        server.host = update.host
    if update.port is not None:
        server.port = update.port
    if update.username is not None:
        server.username = update.username
    if update.is_active is not None:
        server.is_active = update.is_active

    if update.private_key is not None:
        server.encrypted_private_key = ssh_service.encrypt_secret(update.private_key)
        server.use_key_auth = True
    if update.password is not None:
        server.encrypted_password = ssh_service.encrypt_secret(update.password)

    db.commit()
    return {"status": "updated"}


@router.delete("/{server_id}")
async def delete_server(
    server_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)
):
    server = (
        db.query(SSHServer)
        .filter(SSHServer.id == server_id, SSHServer.user_id == int(user["sub"]))
        .first()
    )

    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    db.delete(server)
    db.commit()
    return {"status": "deleted"}


@router.post("/{server_id}/health")
async def check_server_health(
    server_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)
):
    server = (
        db.query(SSHServer)
        .filter(SSHServer.id == server_id, SSHServer.user_id == int(user["sub"]))
        .first()
    )

    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if not ssh_service:
        raise HTTPException(status_code=500, detail="SSH service not initialized")

    client = get_ssh_connection(server, ssh_service)

    try:
        health = ssh_service.check_health(client)
        metrics = ssh_service.get_server_metrics(client)
        instances = ssh_service.list_instances(client)

        server.health_status = health["status"]
        server.last_health_check = datetime.utcnow()
        db.commit()

        if health["status"] == "healthy":
            metric = ServerMetrics(
                server_id=server.id,
                cpu_percent=metrics.get("cpu_percent", 0),
                memory_total_mb=metrics.get("memory", {}).get("total", 0),
                memory_used_mb=metrics.get("memory", {}).get("used", 0),
                disk_total_gb=0,
                disk_used_gb=0,
                docker_containers_total=metrics.get("containers_total", 0),
                docker_containers_running=metrics.get("containers_running", 0),
            )
            db.add(metric)
            db.commit()

        return {
            "server_id": server.id,
            "status": health["status"],
            "metrics": metrics,
            "instances": instances,
            "checked_at": datetime.utcnow().isoformat(),
        }
    finally:
        client.close()


@router.get("/{server_id}/instances")
async def list_server_instances(
    server_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)
):
    server = (
        db.query(SSHServer)
        .filter(SSHServer.id == server_id, SSHServer.user_id == int(user["sub"]))
        .first()
    )

    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if not ssh_service:
        raise HTTPException(status_code=500, detail="SSH service not initialized")

    client = get_ssh_connection(server, ssh_service)

    try:
        instances = ssh_service.list_instances(client)
        return instances
    finally:
        client.close()


@router.post("/{server_id}/instances")
async def create_instance_on_server(
    server_id: int,
    instance_data: InstanceCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    server = (
        db.query(SSHServer)
        .filter(SSHServer.id == server_id, SSHServer.user_id == int(user["sub"]))
        .first()
    )

    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if not ssh_service:
        raise HTTPException(status_code=500, detail="SSH service not initialized")

    client = get_ssh_connection(server, ssh_service)

    try:
        instance_name = instance_data.name or f"mt5-{random.randint(1000, 9999)}"

        result = ssh_service.run_mt5_instance(
            client, instance_name, instance_data.image
        )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        instance = Instance(
            id=result["container_id"],
            name=instance_name,
            user_id=int(user["sub"]),
            server_id=server.id,
            docker_container_id=result["container_id"],
            status="running",
            rpyc_port=result.get("rpyc_port"),
            vnc_port=result.get("vnc_port"),
        )
        db.add(instance)
        db.commit()

        return {
            "id": result["container_id"],
            "name": instance_name,
            "server": server.name,
            "status": "created",
            "rpyc_port": result.get("rpyc_port"),
            "vnc_port": result.get("vnc_port"),
        }
    finally:
        client.close()


@router.post("/{server_id}/instances/{instance_name}/{action}")
async def control_instance_on_server(
    server_id: int,
    instance_name: str,
    action: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    server = (
        db.query(SSHServer)
        .filter(SSHServer.id == server_id, SSHServer.user_id == int(user["sub"]))
        .first()
    )

    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if not ssh_service:
        raise HTTPException(status_code=500, detail="SSH service not initialized")

    client = get_ssh_connection(server, ssh_service)

    try:
        result = ssh_service.control_instance(client, instance_name, action)
        return result
    finally:
        client.close()


@router.get("/{server_id}/instances/{instance_name}/logs")
async def get_instance_logs(
    server_id: int,
    instance_name: str,
    lines: int = Query(100, ge=1, le=10000),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    server = (
        db.query(SSHServer)
        .filter(SSHServer.id == server_id, SSHServer.user_id == int(user["sub"]))
        .first()
    )

    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if not ssh_service:
        raise HTTPException(status_code=500, detail="SSH service not initialized")

    client = get_ssh_connection(server, ssh_service)

    try:
        logs = ssh_service.get_instance_logs(client, instance_name, lines)
        return {"logs": logs.split("\n")}
    finally:
        client.close()
