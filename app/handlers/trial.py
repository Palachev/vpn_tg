from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.types import Message

from app.repositories.user_repository import UserRepository
from app.services.subscription import SubscriptionService

router = Router()


@router.message(F.text == "🆓 Пробный период")
async def start_trial(
    message: Message,
    subscription_service: SubscriptionService,
    user_repo: UserRepository,
) -> None:
    marked = await user_repo.try_mark_trial_used(message.from_user.id)
    if not marked:
        await message.answer("Пробный период уже был использован. Оформи подписку.")
        return
    user = await subscription_service.provision_trial(message.from_user.id)
    if user.subscription_link:
        safe_link = html.escape(user.subscription_link)
        await message.answer(
            "✅ Пробный период активирован!\n\n"
            "Вот твоя ссылка для подключения:\n"
            f"https://deeplink.website/link?url_ha=https://panel.dagdev.ru<code>{safe_link}</code>"
        )
        return
    await message.answer(
        "✅ Пробный период активирован, но ссылка пока не готова. Напиши в поддержку."
    )
