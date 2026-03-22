from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import Response
import httpx
import asyncio
import websockets
import logging

from app.auth.jwt import verify_token
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_vnc_port(instance_id: str) -> str:
    """Get the host-mapped VNC port for a container."""
    import docker

    client = docker.from_env()
    try:
        container = client.containers.get(instance_id)
        port_bindings = container.ports.get("6081/tcp")
        if not port_bindings:
            raise HTTPException(status_code=400, detail="VNC port not exposed")
        return port_bindings[0]["HostPort"]
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Instance not found")


@router.get("/{instance_id}/status")
async def vnc_status(instance_id: str):
    try:
        vnc_port = _get_vnc_port(instance_id)
    except HTTPException as e:
        if e.status_code == 400:
            return {"status": "not_exposed", "instance_id": instance_id}
        raise

    async with httpx.AsyncClient(timeout=5) as http_client:
        try:
            resp = await http_client.get(f"http://localhost:{vnc_port}/")
            return {
                "status": "available" if resp.status_code == 200 else "error",
                "instance_id": instance_id,
                "vnc_url": f"/api/v1/vnc/{instance_id}/proxy/vnc.html",
                "port": vnc_port,
            }
        except Exception:
            return {"status": "unreachable", "instance_id": instance_id}


@router.get("/{instance_id}/screenshot")
async def get_screenshot(instance_id: str):
    return {
        "message": "Screenshot capture requires VNC snapshot agent",
        "instance_id": instance_id,
    }


@router.get("/{instance_id}/proxy/{path:path}")
async def vnc_proxy(instance_id: str, path: str, request: Request):
    """Reverse proxy HTTP requests to the container's noVNC server."""
    vnc_port = _get_vnc_port(instance_id)
    target_url = f"http://localhost:{vnc_port}/{path}"

    if request.query_params:
        target_url += f"?{request.query_params}"

    async with httpx.AsyncClient(timeout=30) as http_client:
        try:
            resp = await http_client.get(
                target_url,
                headers={
                    k: v
                    for k, v in request.headers.items()
                    if k.lower() not in ("host", "connection")
                },
            )

            content_type = resp.headers.get("content-type", "application/octet-stream")

            return Response(
                content=resp.content,
                status_code=resp.status_code,
                media_type=content_type,
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=502, detail="noVNC server not reachable in container"
            )
        except Exception as e:
            logger.error(f"VNC proxy error: {e}")
            raise HTTPException(status_code=502, detail="VNC proxy error")


@router.websocket("/{instance_id}/proxy/websockify")
async def vnc_websocket_proxy(websocket: WebSocket, instance_id: str):
    """WebSocket proxy for noVNC -> container's websockify."""
    vnc_port = _get_vnc_port(instance_id)
    ws_url = f"ws://localhost:{vnc_port}/websockify"

    await websocket.accept()

    try:
        async with websockets.connect(
            ws_url,
            subprotocols=["binary"],
            max_size=2**23,
            ping_interval=None,
        ) as upstream:

            async def client_to_upstream():
                try:
                    while True:
                        data = await websocket.receive_bytes()
                        await upstream.send(data)
                except Exception:
                    pass

            async def upstream_to_client():
                try:
                    async for message in upstream:
                        if isinstance(message, bytes):
                            await websocket.send_bytes(message)
                        else:
                            await websocket.send_text(message)
                except Exception:
                    pass

            await asyncio.gather(client_to_upstream(), upstream_to_client())

    except Exception as e:
        logger.error(f"VNC WebSocket proxy error: {e}")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
