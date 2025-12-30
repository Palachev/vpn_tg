from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.keyboards.admin import admin_panel_keyboard
from app.repositories.payment_repository import PaymentRepository
from app.repositories.user_repository import UserRepository

router = Router()


def _is_admin(user_id: int, settings: Settings) -> bool:
    return user_id in settings.telegram_admin_ids


async def _render_stats(user_repo: UserRepository, payment_repo: PaymentRepository) -> str:
    total_users = await user_repo.count_users()
    active_users = await user_repo.count_active_subscriptions(datetime.utcnow().isoformat())
    paid_count = await payment_repo.count_paid_invoices()
    paid_total = await payment_repo.sum_paid_amount()
    return (
        "Админ-панель\n\n"
        f"Пользователей всего: {total_users}\n"
        f"Активных подписок: {active_users}\n"
        f"Оплат успешно: {paid_count}\n"
        f"Выручка (в валюте): {paid_total:.2f}"
    )


@router.message(Command("admin"))
async def admin_panel(
    message: Message,
    settings: Settings,
    user_repo: UserRepository,
    payment_repo: PaymentRepository,
) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer("Доступ запрещён.")
        return
    text = await _render_stats(user_repo, payment_repo)
    await message.answer(text, reply_markup=admin_panel_keyboard())


@router.callback_query(F.data.in_(["admin:stats", "admin:refresh"]))
async def admin_refresh(
    callback: CallbackQuery,
    settings: Settings,
    user_repo: UserRepository,
    payment_repo: PaymentRepository,
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    text = await _render_stats(user_repo, payment_repo)
    await callback.message.edit_text(text, reply_markup=admin_panel_keyboard())
    await callback.answer()
