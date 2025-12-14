from __future__ import annotations

import asyncio
import logging
from aiohttp import web

from aiogram import Bot, Dispatcher

from app.config import Settings
from app.db import Database
from app.handlers import help, install, purchase, referral, renew, start, status
from app.repositories.payment_repository import PaymentRepository
from app.repositories.referral_repository import ReferralRepository
from app.repositories.user_repository import UserRepository
from app.server import WebhookApp
from app.services.context import DependencyMiddleware
from app.services.marzban import MarzbanService
from app.services.payments import PaymentService
from app.services.referral import ReferralService
from app.services.subscription import SubscriptionService

logging.basicConfig(level=logging.INFO)


async def start_webhook_app(app: web.Application, host: str = "0.0.0.0", port: int = 8080) -> None:
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()


async def main() -> None:
    settings = Settings()
    db = Database(settings.database_path)
    await db.connect()

    user_repo = UserRepository(db)
    payment_repo = PaymentRepository(db)
    referral_repo = ReferralRepository(db)

    marzban = MarzbanService(settings.marzban_base_url, settings.marzban_api_key)
    payment_service = PaymentService(settings, payment_repo)
    referral_service = ReferralService(settings, referral_repo)
    subscription_service = SubscriptionService(settings, user_repo, payment_repo, marzban)

    bot = Bot(token=settings.telegram_token, parse_mode="HTML")
    dp = Dispatcher()

    bot_info = await bot.get_me()
    dp.message.middleware(DependencyMiddleware(
        payment_service=payment_service,
        subscription_service=subscription_service,
        referral_service=referral_service,
        bot_username=bot_info.username,
    ))
    dp.callback_query.middleware(DependencyMiddleware(
        payment_service=payment_service,
        subscription_service=subscription_service,
        referral_service=referral_service,
        bot_username=bot_info.username,
    ))

    dp.include_router(start.router)
    dp.include_router(purchase.router)
    dp.include_router(install.router)
    dp.include_router(status.router)
    dp.include_router(renew.router)
    dp.include_router(referral.router)
    dp.include_router(help.router)

    webhook_app = WebhookApp(payment_service, subscription_service, settings.webhook_path).build()

    await asyncio.gather(
        start_webhook_app(webhook_app),
        dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
