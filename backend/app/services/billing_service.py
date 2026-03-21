import stripe
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

TIER_CONFIGS = {
    "free": {
        "name": "Free",
        "price_monthly": 0,
        "price_yearly": 0,
        "limits": {
            "max_servers": 1,
            "max_instances": 1,
            "max_api_calls_per_day": 1000,
            "max_users": 1,
            "support_level": "community",
        },
        "features": [
            "1 MT5 instance",
            "Basic monitoring",
            "Community support",
            "1,000 API calls/day",
        ],
    },
    "basic": {
        "name": "Basic",
        "price_monthly": 2900,
        "price_yearly": 29000,
        "stripe_price_monthly": "price_basic_monthly",
        "stripe_price_yearly": "price_basic_yearly",
        "limits": {
            "max_servers": 3,
            "max_instances": 5,
            "max_api_calls_per_day": 10000,
            "max_users": 3,
            "support_level": "email",
        },
        "features": [
            "5 MT5 instances",
            "3 servers",
            "Telegram alerts",
            "Email support",
            "10,000 API calls/day",
        ],
    },
    "pro": {
        "name": "Pro",
        "price_monthly": 7900,
        "price_yearly": 79000,
        "stripe_price_monthly": "price_pro_monthly",
        "stripe_price_yearly": "price_pro_yearly",
        "limits": {
            "max_servers": 10,
            "max_instances": 25,
            "max_api_calls_per_day": 100000,
            "max_users": 10,
            "support_level": "priority",
        },
        "features": [
            "25 MT5 instances",
            "10 servers",
            "Copy trading API",
            "Priority support",
            "Webhook integration",
            "100,000 API calls/day",
        ],
    },
    "enterprise": {
        "name": "Enterprise",
        "price_monthly": 0,
        "price_yearly": 0,
        "limits": {
            "max_servers": -1,
            "max_instances": -1,
            "max_api_calls_per_day": -1,
            "max_users": -1,
            "support_level": "dedicated",
        },
        "features": [
            "Unlimited instances",
            "Unlimited servers",
            "Dedicated support",
            "Custom integrations",
            "SLA guarantee",
            "White-label option",
        ],
    },
}


class BillingService:
    def __init__(self, stripe_secret_key: str, webhook_secret: str):
        stripe.api_key = stripe_secret_key
        self.webhook_secret = webhook_secret

    def create_customer(
        self, email: str, name: str = None, user_id: int = None
    ) -> Optional[str]:
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={"user_id": str(user_id)} if user_id else {},
            )
            return customer.id
        except Exception as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            return None

    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        trial_days: int = 14,
    ) -> Optional[Dict]:
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[{"price": price_id, "quantity": 1}],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                trial_period_days=trial_days,
                subscription_data={"trial_period_days": trial_days},
            )
            return {"session_id": session.id, "url": session.url}
        except Exception as e:
            logger.error(f"Failed to create checkout session: {e}")
            return None

    def create_customer_portal_session(
        self, customer_id: str, return_url: str
    ) -> Optional[str]:
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id, return_url=return_url
            )
            return session.url
        except Exception as e:
            logger.error(f"Failed to create portal session: {e}")
            return None

    def cancel_subscription(
        self, subscription_id: str, cancel_at_period_end: bool = True
    ) -> bool:
        try:
            if cancel_at_period_end:
                stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
            else:
                stripe.Subscription.delete(subscription_id)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False

    def reactivate_subscription(self, subscription_id: str) -> bool:
        try:
            stripe.Subscription.modify(subscription_id, cancel_at_period_end=False)
            return True
        except Exception as e:
            logger.error(f"Failed to reactivate subscription: {e}")
            return False

    def get_subscription(self, subscription_id: str) -> Optional[Dict]:
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": sub.id,
                "status": sub.status,
                "current_period_start": datetime.fromtimestamp(
                    sub.current_period_start
                ),
                "current_period_end": datetime.fromtimestamp(sub.current_period_end),
                "cancel_at_period_end": sub.cancel_at_period_end,
                "items": [
                    {"price_id": item.price.id, "quantity": item.quantity}
                    for item in sub.items.data
                ],
            }
        except Exception as e:
            logger.error(f"Failed to get subscription: {e}")
            return None

    def get_invoices(self, customer_id: str, limit: int = 10) -> List[Dict]:
        try:
            invoices = stripe.Invoice.list(customer=customer_id, limit=limit)
            return [
                {
                    "id": inv.id,
                    "amount": inv.amount_paid,
                    "currency": inv.currency,
                    "status": inv.status,
                    "invoice_url": inv.hosted_invoice_url,
                    "pdf_url": inv.invoice_pdf,
                    "created": datetime.fromtimestamp(inv.created),
                    "period_start": datetime.fromtimestamp(inv.period_start)
                    if inv.period_start
                    else None,
                    "period_end": datetime.fromtimestamp(inv.period_end)
                    if inv.period_end
                    else None,
                }
                for inv in invoices.data
            ]
        except Exception as e:
            logger.error(f"Failed to get invoices: {e}")
            return []

    def record_usage(
        self, subscription_item_id: str, quantity: int, timestamp: int = None
    ) -> bool:
        try:
            stripe.UsageRecord.create(
                subscription_item_id=subscription_item_id,
                quantity=quantity,
                timestamp=timestamp or int(datetime.utcnow().timestamp()),
            )
            return True
        except Exception as e:
            logger.error(f"Failed to record usage: {e}")
            return False

    def handle_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )

            handler_map = {
                "checkout.session.completed": self._handle_checkout_completed,
                "customer.subscription.created": self._handle_subscription_created,
                "customer.subscription.updated": self._handle_subscription_updated,
                "customer.subscription.deleted": self._handle_subscription_deleted,
                "invoice.paid": self._handle_invoice_paid,
                "invoice.payment_failed": self._handle_invoice_failed,
            }

            handler = handler_map.get(event["type"])
            if handler:
                return handler(event["data"]["object"])

            return {"status": "unhandled", "type": event["type"]}

        except stripe.error.SignatureVerificationError:
            return {"status": "error", "message": "Invalid signature"}
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return {"status": "error", "message": str(e)}

    def _handle_checkout_completed(self, session: Dict) -> Dict:
        logger.info(f"Checkout completed: {session.get('id')}")
        return {"status": "processed", "type": "checkout.completed"}

    def _handle_subscription_created(self, subscription: Dict) -> Dict:
        logger.info(f"Subscription created: {subscription.get('id')}")
        return {"status": "processed", "type": "subscription.created"}

    def _handle_subscription_updated(self, subscription: Dict) -> Dict:
        logger.info(f"Subscription updated: {subscription.get('id')}")
        return {"status": "processed", "type": "subscription.updated"}

    def _handle_subscription_deleted(self, subscription: Dict) -> Dict:
        logger.info(f"Subscription deleted: {subscription.get('id')}")
        return {"status": "processed", "type": "subscription.deleted"}

    def _handle_invoice_paid(self, invoice: Dict) -> Dict:
        logger.info(f"Invoice paid: {invoice.get('id')}")
        return {"status": "processed", "type": "invoice.paid"}

    def _handle_invoice_failed(self, invoice: Dict) -> Dict:
        logger.warning(f"Invoice failed: {invoice.get('id')}")
        return {"status": "processed", "type": "invoice.payment_failed"}

    def check_usage_limits(
        self, user_id: int, tier: str, current_usage: Dict[str, int]
    ) -> Dict[str, Any]:
        limits = TIER_CONFIGS.get(tier, TIER_CONFIGS["free"])["limits"]

        violations = []
        for metric, limit in limits.items():
            if limit == -1:
                continue
            current = current_usage.get(metric, 0)
            if current >= limit:
                violations.append(
                    {"metric": metric, "limit": limit, "current": current}
                )

        return {
            "within_limits": len(violations) == 0,
            "violations": violations,
            "tier": tier,
            "limits": limits,
        }

    def get_tier_config(self, tier: str) -> Dict[str, Any]:
        return TIER_CONFIGS.get(tier, TIER_CONFIGS["free"])


billing_service: Optional[BillingService] = None


def init_billing_service(stripe_secret_key: str, webhook_secret: str):
    global billing_service
    billing_service = BillingService(stripe_secret_key, webhook_secret)
    return billing_service
