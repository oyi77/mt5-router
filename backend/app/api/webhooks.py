from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import hmac
import hashlib
import json

from app.core.database import get_db
from app.models.database import User, WebhookConfig as DBWebhookConfig
from app.auth.jwt import get_current_user

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])
logger = logging.getLogger(__name__)


class WebhookConfig(BaseModel):
    id: int
    user_id: int
    name: str
    url: str
    secret: Optional[str]
    events: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookCreate(BaseModel):
    name: str
    url: str
    secret: Optional[str] = None
    events: List[str]


class WebhookEvent(BaseModel):
    event_type: str
    payload: dict
    timestamp: datetime = datetime.utcnow()


@router.post("/receive")
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        logger.info(f"Received webhook: {payload}")

        signal_data = {
            "symbol": payload.get("symbol", payload.get("ticker", "")),
            "action": payload.get("action", payload.get("direction", "")).upper(),
            "volume": float(payload.get("volume", payload.get("qty", 0.01))),
            "price": float(payload.get("price", 0)),
        }

        if not signal_data["symbol"]:
            return {"status": "ignored", "reason": "no symbol"}

        logger.info(f"Processed signal: {signal_data}")

        return {"status": "received", "signal": signal_data}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/configure")
async def configure_webhook(
    webhook: WebhookCreate,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = user.get("id")

    webhook_config = DBWebhookConfig(
        user_id=user_id,
        name=webhook.name,
        url=webhook.url,
        secret=webhook.secret,
        events=json.dumps(webhook.events),
        is_active=True,
    )
    db.add(webhook_config)
    db.commit()
    db.refresh(webhook_config)

    return {"id": webhook_config.id, "status": "created"}


@router.get("")
async def list_webhooks(
    user: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    user_id = user.get("id")
    webhooks = (
        db.query(DBWebhookConfig).filter(DBWebhookConfig.user_id == user_id).all()
    )
    return [
        {
            "id": w.id,
            "name": w.name,
            "url": w.url,
            "events": json.loads(w.events) if w.events else [],
            "is_active": w.is_active,
        }
        for w in webhooks
    ]


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = user.get("id")

    webhook = (
        db.query(DBWebhookConfig)
        .filter(DBWebhookConfig.id == webhook_id, DBWebhookConfig.user_id == user_id)
        .first()
    )

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    db.delete(webhook)
    db.commit()

    return {"status": "deleted"}


@router.post("/test/{webhook_id}")
async def test_webhook(
    webhook_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    webhook = (
        db.query(DBWebhookConfig)
        .filter(
            DBWebhookConfig.id == webhook_id, DBWebhookConfig.user_id == user.get("id")
        )
        .first()
    )

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    import httpx

    test_payload = {
        "event": "test",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Test webhook from MT5 Router",
    }

    try:
        headers = {"Content-Type": "application/json"}
        if webhook.secret:
            body = json.dumps(test_payload)
            signature = hmac.new(
                webhook.secret.encode(), body.encode(), hashlib.sha256
            ).hexdigest()
            headers["X-Signature"] = signature

        response = httpx.post(
            webhook.url, json=test_payload, headers=headers, timeout=10
        )
        return {"status": "success", "response_code": response.status_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}
