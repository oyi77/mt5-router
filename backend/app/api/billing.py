from fastapi import APIRouter, Depends, HTTPException, Request, Query
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.models.database import (
    User,
    Subscription,
    Invoice as InvoiceModel,
    SSHServer,
    Instance as InstanceModel,
)
from app.auth.jwt import get_current_user
from app.services.billing_service import billing_service, TIER_CONFIGS

router = APIRouter()
logger = logging.getLogger(__name__)


class CheckoutRequest(BaseModel):
    tier: str
    billing_period: str = "monthly"


def get_user_from_token(token: dict, db: Session) -> User:
    user_id = int(token["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/tiers")
async def list_tiers():
    return {
        name: {
            "name": config["name"],
            "price_monthly": config["price_monthly"] / 100,
            "price_yearly": config["price_yearly"] / 100,
            "limits": config["limits"],
            "features": config["features"],
        }
        for name, config in TIER_CONFIGS.items()
        if name != "enterprise"
    }


@router.get("/subscription")
async def get_subscription(
    token: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    user = get_user_from_token(token, db)
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()

    if not sub:
        return {
            "tier": "free",
            "status": "active",
            "limits": TIER_CONFIGS["free"]["limits"],
            "features": TIER_CONFIGS["free"]["features"],
        }

    config = TIER_CONFIGS.get(sub.tier, TIER_CONFIGS["free"])

    return {
        "tier": sub.tier,
        "status": sub.status,
        "current_period_end": sub.current_period_end.isoformat()
        if sub.current_period_end
        else None,
        "cancel_at_period_end": sub.cancel_at_period_end,
        "stripe_customer_id": sub.stripe_customer_id,
        "limits": config["limits"],
        "features": config["features"],
    }


@router.post("/checkout")
async def create_checkout(
    checkout: CheckoutRequest,
    token: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not billing_service:
        raise HTTPException(status_code=500, detail="Billing not configured")

    tier_config = TIER_CONFIGS.get(checkout.tier)
    if not tier_config:
        raise HTTPException(status_code=400, detail="Invalid tier")

    user = get_user_from_token(token, db)
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()

    if not sub or not sub.stripe_customer_id:
        customer_id = billing_service.create_customer(
            email=user.email, name=user.full_name or user.username, user_id=user.id
        )
        if not customer_id:
            raise HTTPException(status_code=500, detail="Failed to create customer")

        if not sub:
            sub = Subscription(user_id=user.id, stripe_customer_id=customer_id)
            db.add(sub)
        else:
            sub.stripe_customer_id = customer_id
        db.commit()
    else:
        customer_id = sub.stripe_customer_id

    price_key = f"stripe_price_{checkout.billing_period}"
    price_id = tier_config.get(price_key)

    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid billing period")

    session = billing_service.create_checkout_session(
        customer_id=customer_id,
        price_id=price_id,
        success_url="https://mt-oc.aitradepulse.com/billing/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="https://mt-oc.aitradepulse.com/billing/cancel",
        trial_days=14,
    )

    if not session:
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

    return session


@router.get("/portal")
async def customer_portal(
    token: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    if not billing_service:
        raise HTTPException(status_code=500, detail="Billing not configured")

    user = get_user_from_token(token, db)
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()

    if not sub or not sub.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found")

    portal_url = billing_service.create_customer_portal_session(
        customer_id=sub.stripe_customer_id,
        return_url="https://mt-oc.aitradepulse.com/billing",
    )

    if not portal_url:
        raise HTTPException(status_code=500, detail="Failed to create portal session")

    return {"url": portal_url}


@router.post("/cancel")
async def cancel_subscription(
    immediate: bool = False,
    token: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not billing_service:
        raise HTTPException(status_code=500, detail="Billing not configured")

    user = get_user_from_token(token, db)
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()

    if not sub or not sub.stripe_subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription")

    success = billing_service.cancel_subscription(
        sub.stripe_subscription_id, cancel_at_period_end=not immediate
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")

    sub.cancel_at_period_end = not immediate
    db.commit()

    return {
        "status": "canceled",
        "cancel_at_period_end": not immediate,
        "message": "Subscription will end at period end"
        if not immediate
        else "Subscription canceled immediately",
    }


@router.post("/reactivate")
async def reactivate_subscription(
    token: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    if not billing_service:
        raise HTTPException(status_code=500, detail="Billing not configured")

    user = get_user_from_token(token, db)
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()

    if not sub or not sub.stripe_subscription_id:
        raise HTTPException(status_code=400, detail="No subscription found")

    if not sub.cancel_at_period_end:
        return {"status": "already_active", "message": "Subscription is already active"}

    success = billing_service.reactivate_subscription(sub.stripe_subscription_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to reactivate subscription")

    sub.cancel_at_period_end = False
    db.commit()

    return {"status": "reactivated", "message": "Subscription reactivated"}


@router.get("/invoices")
async def list_invoices(
    limit: int = Query(10, ge=1, le=100),
    token: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not billing_service:
        raise HTTPException(status_code=500, detail="Billing not configured")

    user = get_user_from_token(token, db)
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()

    if not sub or not sub.stripe_customer_id:
        return []

    invoices = billing_service.get_invoices(sub.stripe_customer_id, limit)
    return invoices


@router.get("/usage")
async def get_usage(
    token: dict = Depends(get_current_user), db: Session = Depends(get_db)
):
    from datetime import datetime, timedelta

    user = get_user_from_token(token, db)
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    tier = sub.tier if sub else "free"

    server_count = db.query(SSHServer).filter(SSHServer.user_id == user.id).count()
    instance_count = (
        db.query(InstanceModel).filter(InstanceModel.user_id == user.id).count()
    )

    limits = TIER_CONFIGS.get(tier, TIER_CONFIGS["free"])["limits"]

    return {
        "tier": tier,
        "usage": {
            "servers": {
                "current": server_count,
                "limit": limits["max_servers"],
                "unlimited": limits["max_servers"] == -1,
            },
            "instances": {
                "current": instance_count,
                "limit": limits["max_instances"],
                "unlimited": limits["max_instances"] == -1,
            },
        },
        "period": {
            "start": datetime.utcnow().replace(day=1).isoformat(),
            "end": (datetime.utcnow().replace(day=1) + timedelta(days=30)).isoformat(),
        },
    }


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    if not billing_service:
        return {"status": "error", "message": "Billing not configured"}

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        return {"status": "error", "message": "Missing signature"}

    result = billing_service.handle_webhook(payload, sig_header)

    if result.get("status") == "processed":
        event_type = result.get("type")
        logger.info(f"Processed webhook event: {event_type}")

    return result
