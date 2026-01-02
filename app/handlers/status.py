from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.types import Message

from app.keyboards.common import renew_keyboard
from app.services.subscription import SubscriptionService

router = Router()


@router.message(F.text == "📊 Статус")
async def show_status(message: Message, subscription_service: SubscriptionService) -> None:
    user = await subscription_service.get_status(message.from_user.id)
    if not user or not user.subscription_expires_at:
        await message.answer(
            "Подписка не активна. Оформи доступ за пару минут.", reply_markup=renew_keyboard()
        )
        return
    text = (
        "Текущая подписка:\n"
        f"Активна до: {user.subscription_expires_at:%d.%m.%Y}\n"
        f"Лимит трафика: {user.traffic_limit_gb or '∞'} GB\n"
        "Если интернет в мобильной сети капризничает — переключись на Mobile сервер."
    )
    if user.subscription_link:
        safe_link = html.escape(user.subscription_link)
        text = (
            f"{text}\n\n"
            "Ссылка для подключения:\n"
            f"<code>{safe_link}</code>"
        )
    await message.answer(text, reply_markup=renew_keyboard())
