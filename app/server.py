from __future__ import annotations

from aiohttp import web
from aiogram import Bot

from app.services.payments import PaymentService
from app.services.subscription import SubscriptionService


class WebhookApp:
    def __init__(
        self,
        bot: Bot,
        payment_service: PaymentService,
        subscription_service: SubscriptionService,
        webhook_path: str,
    ):
        self.bot = bot
        self.payment_service = payment_service
        self.subscription_service = subscription_service
        self.webhook_path = webhook_path

    def build(self) -> web.Application:
        app = web.Application()
        app.add_routes([web.post(self.webhook_path, self.handle_payment)])
        return app

    async def handle_payment(self, request: web.Request) -> web.Response:
        content_type = request.content_type or ""
        result = None
        if content_type.startswith("application/json"):
            payload = await request.text()
            signature = request.headers.get("X-Signature", "")
            result = await self.payment_service.verify_webhook(payload, signature)
        else:
            form = await request.post()
            result = await self.payment_service.verify_robokassa(dict(form))
        if not result:
            return web.json_response({"status": "ignored"}, status=400)
        try:
            user = await self.subscription_service.process_payment_success(result.invoice_id)
        except aiohttp.ClientResponseError as exc:
            return web.json_response(
                {"status": "marzban_error", "code": exc.status, "message": exc.message},
                status=502,
            )
        if not user:
            return web.json_response({"status": "not_found"}, status=404)
        await self._send_access_message(user.telegram_id, user.subscription_link or "")
        if not content_type.startswith("application/json"):
            return web.Response(text=f"OK{result.invoice_id}")
        return web.json_response({"status": "ok", "user": user.marzban_username})
