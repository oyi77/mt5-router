import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.telegram_token = None
        self.telegram_chat_id = None
        self.webhook_urls = {}

    def configure_telegram(self, token: str, chat_id: str):
        self.telegram_token = token
        self.telegram_chat_id = chat_id

    def add_webhook(self, name: str, url: str, events: List[str]):
        self.webhook_urls[name] = {"url": url, "events": events, "active": True}

    async def send_telegram(self, message: str, parse_mode: str = "HTML") -> bool:
        if not self.telegram_token or not self.telegram_chat_id:
            logger.warning("Telegram not configured")
            return False

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": parse_mode,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=10)
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False

    async def send_webhook(self, event: str, data: Dict[str, Any]) -> bool:
        success = True
        for name, config in self.webhook_urls.items():
            if not config["active"] or event not in config["events"]:
                continue

            payload = {
                "event": event,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data,
            }

            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(config["url"], json=payload, timeout=10)
                    if resp.status_code >= 400:
                        logger.error(f"Webhook {name} failed: {resp.status_code}")
                        success = False
            except Exception as e:
                logger.error(f"Webhook {name} error: {e}")
                success = False

        return success

    async def notify(
        self, event: str, data: Dict[str, Any], channels: List[str] = None
    ) -> Dict[str, bool]:
        results = {}
        message = self._format_message(event, data)

        if channels is None or "telegram" in channels:
            results["telegram"] = await self.send_telegram(message)

        if channels is None or "webhook" in channels:
            results["webhook"] = await self.send_webhook(event, data)

        return results

    def _format_message(self, event: str, data: Dict[str, Any]) -> str:
        if event == "order_executed":
            return (
                f"📊 <b>Order Executed</b>\n"
                f"Symbol: {data.get('symbol')}\n"
                f"Type: {data.get('order_type')}\n"
                f"Volume: {data.get('volume')}\n"
                f"Price: {data.get('price')}\n"
                f"Ticket: {data.get('ticket')}"
            )
        elif event == "position_closed":
            pnl = data.get("profit", 0)
            emoji = "✅" if pnl >= 0 else "❌"
            return (
                f"{emoji} <b>Position Closed</b>\n"
                f"Symbol: {data.get('symbol')}\n"
                f"P&L: ${pnl:.2f}\n"
                f"Ticket: {data.get('ticket')}"
            )
        elif event == "price_alert":
            return (
                f"🔔 <b>Price Alert</b>\n"
                f"Symbol: {data.get('symbol')}\n"
                f"Condition: {data.get('condition')}\n"
                f"Current Price: {data.get('price')}"
            )
        elif event == "margin_call":
            return (
                f"⚠️ <b>MARGIN WARNING</b>\n"
                f"Account: {data.get('account')}\n"
                f"Margin Level: {data.get('margin_level')}%\n"
                f"Free Margin: ${data.get('free_margin'):.2f}"
            )
        elif event == "instance_status":
            return (
                f"🖥️ <b>Instance {data.get('status')}</b>\n"
                f"Name: {data.get('name')}\n"
                f"ID: {data.get('id')}"
            )
        else:
            return f"📢 <b>{event}</b>\n{json.dumps(data, indent=2)}"


notification_service = NotificationService()
