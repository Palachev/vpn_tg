from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.config import Settings
from app.keyboards.admin import admin_broadcast_keyboard, admin_panel_keyboard
from app.repositories.payment_repository import PaymentRepository
from app.repositories.user_repository import UserRepository
from app.services.subscription import SubscriptionService

router = Router()


class BroadcastState(StatesGroup):
    waiting_message = State()


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


@router.message(Command("retry_pending"))
async def retry_pending(
    message: Message,
    settings: Settings,
    payment_repo: PaymentRepository,
    subscription_service: SubscriptionService,
) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer("Доступ запрещён.")
        return
    pending = await payment_repo.list_pending_invoices()
    if not pending:
        await message.answer("Нет платежей для повторной выдачи.")
        return
    success = 0
    failed = 0
    for invoice_id in pending:
        try:
            user = await subscription_service.process_payment_success(invoice_id)
            if user:
                success += 1
            else:
                failed += 1
        except Exception:
            failed += 1
    await message.answer(
        "Повторная выдача завершена.\n"
        f"Успешно: {success}\n"
        f"Ошибок: {failed}"
    )


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
async def admin_broadcast_start(
    callback: CallbackQuery,
    settings: Settings,
    state: FSMContext,
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    await state.set_state(BroadcastState.waiting_message)
    await callback.message.edit_text(
        "Отправьте сообщение для рассылки всем пользователям. Можно отправить текст, фото или файл.",
        reply_markup=admin_broadcast_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:cancel_broadcast")
async def admin_broadcast_cancel(
    callback: CallbackQuery,
    settings: Settings,
    user_repo: UserRepository,
    payment_repo: PaymentRepository,
    state: FSMContext,
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    await state.clear()
    text = await _render_stats(user_repo, payment_repo)
    await callback.message.edit_text(f"Рассылка отменена.\n\n{text}", reply_markup=admin_panel_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:back")
async def admin_back_to_panel(
    callback: CallbackQuery,
    settings: Settings,
    user_repo: UserRepository,
    payment_repo: PaymentRepository,
    state: FSMContext,
) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    await state.clear()
    text = await _render_stats(user_repo, payment_repo)
    await callback.message.edit_text(text, reply_markup=admin_panel_keyboard())
    await callback.answer()


@router.message(BroadcastState.waiting_message)
async def admin_broadcast_send(
    message: Message,
    settings: Settings,
    state: FSMContext,
    user_repo: UserRepository,
) -> None:
    if not _is_admin(message.from_user.id, settings):
        await message.answer("Доступ запрещён.")
        return
    user_ids = await user_repo.list_telegram_ids()
    success = 0
    failed = 0
    for user_id in user_ids:
        try:
            await message.copy_to(user_id)
            success += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
    await state.clear()
    await message.answer(
        "Рассылка завершена.\n"
        f"Получателей: {len(user_ids)}\n"
        f"Доставлено: {success}\n"
        f"Ошибок: {failed}",
        reply_markup=admin_panel_keyboard(),
    )
