from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.keyboards.common import main_menu, status_keyboard
from app.services.subscription import SubscriptionService

router = Router()


@router.message(F.text == "📊 Status")
async def show_status(
    message: Message,
    subscription_service: SubscriptionService,
    settings: Settings,
) -> None:
    user = await subscription_service.get_status(message.from_user.id)
    if not user or not user.subscription_expires_at:
        await message.answer("Подписка не активна. Оформи доступ.", reply_markup=status_keyboard(None))
        return
    expires_at = user.subscription_expires_at.strftime("%d.%m.%Y") if user.subscription_expires_at else "—"
    traffic_limit = f"{user.traffic_limit_gb:.0f} GB" if user.traffic_limit_gb else "—"
    server_label = settings.marzban_inbounds[0] if settings.marzban_inbounds else ""
    text_lines = ["🛡 DagDev VPN", "━━━━━━━━━━━━", f"ℹ️ До: {expires_at}", f"📊 Трафик: {traffic_limit}"]
    if server_label:
        text_lines.append(f"ℹ️ Сервер: {server_label}")
    if user.is_stale:
        text_lines.append("ℹ️ Статус обновится позже.")
    text = "\n".join(text_lines)
    await message.answer(text, reply_markup=status_keyboard(user.subscription_link))


@router.callback_query(F.data == "nav:back")
async def nav_back(callback: CallbackQuery) -> None:
    await callback.message.answer("Выбери действие.", reply_markup=main_menu())
    await callback.answer()
