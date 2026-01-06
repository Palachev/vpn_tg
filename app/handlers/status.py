from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.keyboards.common import main_menu, renew_keyboard, status_keyboard
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
    snapshot = await subscription_service.get_status_snapshot(message.from_user.id)
    trial_used, _, _ = await user_repo.get_user_meta(message.from_user.id)
    if not snapshot or not snapshot.user.subscription_expires_at:
        text = "Подписка не активна. Оформи доступ за пару минут."
        if not trial_used:
            text = f"{text}\n\nМожно активировать пробный период."
        if bot_username:
            ref_link = f"https://t.me/{bot_username}?start={message.from_user.id}"
            text = f"{text}\n\nПригласи друга: {ref_link}"
        await message.answer(text, reply_markup=renew_keyboard())
        return
    user = snapshot.user
    expires_at = user.subscription_expires_at.strftime("%d.%m.%Y")
    traffic_line = _format_traffic_line(snapshot.traffic_limit_gb, snapshot.traffic_used_gb)
    lines = [
        "🛡 DagDev VPN",
        "━━━━━━━━━━━━",
        "📊 Status",
        f"Active until: {expires_at}",
        traffic_line,
    ]
    if snapshot.server_label:
        lines.append(f"Server: {snapshot.server_label}")
    if snapshot.is_stale:
        lines.append("ℹ️ Data from last sync.")
    text = "\n".join(lines)
    keyboard = status_keyboard(user.subscription_link or "", profile_name="DagDev VPN")
    if not keyboard:
        await message.answer("ℹ️ Access link is not ready yet.")
        await message.answer(text, reply_markup=renew_keyboard())
        return
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "nav:back")
async def nav_back(callback: CallbackQuery) -> None:
    await callback.message.answer("Выбери действие.", reply_markup=main_menu())
    await callback.answer()


def _format_traffic_line(limit_gb: float | None, used_gb: float | None) -> str:
    if limit_gb is None:
        return "Traffic: Unlimited"
    total_text = _format_gb(limit_gb)
    if used_gb is None:
        return f"Traffic: {total_text} total"
    remaining_gb = max(limit_gb - used_gb, 0)
    return (
        f"Traffic: {total_text} total • "
        f"{_format_gb(used_gb)} used • "
        f"{_format_gb(remaining_gb)} left"
    )


def _format_gb(value: float) -> str:
    return f"{value:.1f} GB"
