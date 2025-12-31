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
_pending_broadcast: set[int] = set()


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
        f"Выручка (в валюте): {paid_total:.2f}\n\n"
        "Для рассылки нажми «📣 Рассылка» и отправь сообщение."
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


@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast_prompt(
    callback: CallbackQuery,
    settings: Settings,
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    _pending_broadcast.add(callback.from_user.id)
    await callback.message.answer("Отправь текст рассылки следующим сообщением.")
    await callback.answer()


@router.callback_query(F.data == "admin:cancel")
async def admin_cancel(
    callback: CallbackQuery,
    settings: Settings,
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    _pending_broadcast.discard(callback.from_user.id)
    await callback.answer("Отменено.")


@router.message()
async def admin_broadcast_send(
    message: Message,
    settings: Settings,
    user_repo: UserRepository,
) -> None:
    if message.from_user.id not in _pending_broadcast:
        return
    if not _is_admin(message.from_user.id, settings):
        _pending_broadcast.discard(message.from_user.id)
        return
    if not message.text:
        await message.answer("Нужен текст рассылки. Отправь сообщение текстом.")
        return
    _pending_broadcast.discard(message.from_user.id)
    recipients = await user_repo.list_telegram_ids()
    if not recipients:
        await message.answer("Нет пользователей для рассылки.")
        return
    delivered = 0
    failed = 0
    for telegram_id in recipients:
        try:
            await message.bot.send_message(telegram_id, message.text)
            delivered += 1
        except Exception:
            failed += 1
    await message.answer(f"Рассылка завершена. Доставлено: {delivered}, ошибок: {failed}.")
