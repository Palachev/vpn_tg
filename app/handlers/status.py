from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.keyboards.common import connection_keyboard, main_menu, renew_keyboard
from app.repositories.user_repository import UserRepository
from app.services.subscription import SubscriptionService

router = Router()


@router.message(F.text == "📊 Статус")
async def show_status(
    message: Message,
    subscription_service: SubscriptionService,
    user_repo: UserRepository,
    bot_username: str,
) -> None:
    user = await subscription_service.get_status(message.from_user.id)
    trial_used, _, _ = await user_repo.get_user_meta(message.from_user.id)
    if not user or not user.subscription_expires_at:
        text = "Подписка не активна. Оформи доступ за пару минут."
        if not trial_used:
            text = f"{text}\n\nМожно активировать пробный период."
        if bot_username:
            ref_link = f"https://t.me/{bot_username}?start={message.from_user.id}"
            text = f"{text}\n\nПригласи друга: {ref_link}"
        await message.answer(text, reply_markup=renew_keyboard())
        return
    text = (
        "🛡 DagDev VPN\n"
        "━━━━━━━━━━━━\n"
        "Your VPN is ready.\n"
        "Tap the button below to connect."
    )
    keyboard = connection_keyboard(user.subscription_link or "")
    if not keyboard:
        await message.answer("ℹ️ Access link is not ready yet.")
        await message.answer(text, reply_markup=renew_keyboard())
        return
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "nav:back")
async def nav_back(callback: CallbackQuery) -> None:
    await callback.message.answer("Выбери действие.", reply_markup=main_menu())
    await callback.answer()
