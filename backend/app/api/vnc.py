from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import Response
import httpx
import logging

from app.auth.jwt import verify_token
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{instance_id}/status")
async def vnc_status(instance_id: str):
    import docker

    client = docker.from_env()

    try:
        container = client.containers.get(instance_id)
        vnc_port = container.ports.get("6081/tcp", [{}])[0].get("HostPort")

        if not vnc_port:
            return {"status": "not_exposed", "instance_id": instance_id}

        async with httpx.AsyncClient(timeout=5) as http_client:
            try:
                resp = await http_client.get(f"http://localhost:{vnc_port}/")
                return {
                    "status": "available" if resp.status_code == 200 else "error",
                    "instance_id": instance_id,
                    "vnc_url": f"/api/v1/vnc/{instance_id}/proxy",
                    "port": vnc_port,
                }
            except:
                return {"status": "unreachable", "instance_id": instance_id}
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Instance not found")


@router.get("/{instance_id}/screenshot")
async def get_screenshot(instance_id: str):
    return {
        "message": "Screenshot capture requires VNC snapshot agent",
        "instance_id": instance_id,
    }


@router.get("/{instance_id}/vnc.html")
async def vnc_viewer(instance_id: str):
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>MT5 VNC - {instance_id}</title>
    <style>
        body {{ margin: 0; padding: 0; background: #1a1a2e; }}
        #vnc-container {{ width: 100vw; height: 100vh; }}
        iframe {{ width: 100%; height: 100%; border: none; }}
    </style>
</head>
<body>
    <div id="vnc-container">
        <iframe src="/api/v1/vnc/{instance_id}/proxy/vnc.html?host=localhost&port=auto&path=websockify&autoconnect=true&resize=scale"></iframe>
    </div>
</body>
</html>
"""
    return Response(content=html_content, media_type="text/html")
