from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from app.keyboards.common import connection_keyboard
from app.repositories.user_repository import UserRepository
from app.services.subscription import SubscriptionService

router = Router()


@router.message(F.text == "Пробный период")
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
        keyboard = connection_keyboard(user.subscription_link)
        if keyboard:
            await message.answer(
                "🛡 DagDev VPN\n"
                "━━━━━━━━━━━━\n"
                "Your VPN is ready.\n"
                "Tap the button below to connect.",
                reply_markup=keyboard,
            )
            return
        await message.answer("ℹ️ Access link is not ready yet.")
        return
    await message.answer(
        "ℹ️ Access link is not ready yet."
    )
