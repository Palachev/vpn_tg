from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from app.config import Settings
from app.keyboards.common import connection_keyboard, tariffs_keyboard
from app.repositories.payment_repository import PaymentRepository
from app.services.payments import PaymentService
from app.services.subscription import SubscriptionService

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "💳 Купить VPN")
async def choose_plan(message: Message) -> None:
    await message.answer(
        "Выбери срок подписки. Оплата занимает 1–2 минуты.",
        reply_markup=tariffs_keyboard(),
    )


@router.callback_query(F.data.startswith("buy:"))
async def start_payment(callback: CallbackQuery, payment_service: PaymentService, subscription_service: SubscriptionService) -> None:
    tariff_code = callback.data.split(":", maxsplit=1)[1]
    tariff = subscription_service.get_tariff(tariff_code)
    invoice = await payment_service.create_invoice(callback.from_user.id, tariff_code, tariff.price)
    await callback.message.answer_invoice(
        title="VPN подписка",
        description=f"Тариф: {tariff.title}",
        payload=invoice.invoice_id,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=tariff.title, amount=int(invoice.amount))],
    )
    await callback.answer()


@router.pre_checkout_query()
async def handle_pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def handle_successful_payment(
    message: Message,
    payment_repo: PaymentRepository,
    subscription_service: SubscriptionService,
    settings: Settings,
) -> None:
    payment = message.successful_payment
    payload_to_tariff = {
        "vpn_1m": "m1",
        "vpn_3m": "m3",
        "vpn_6m": "m6",
        "vpn_12m": "m12",
    }
    tariff_code = payload_to_tariff.get(payment.invoice_payload)
    if not tariff_code:
        await message.answer("Платеж получен, но тариф не найден. Напиши в поддержку.")
        return
    invoice_id = payment.telegram_payment_charge_id
    await payment_repo.create_invoice(
        invoice_id,
        message.from_user.id,
        tariff_code,
        float(payment.total_amount),
        payment.currency,
    )
    try:
        user = await subscription_service.process_payment_success(invoice_id)
    except Exception as exc:
        logger.exception("Failed to provision after payment: invoice_id=%s", invoice_id)
        await payment_repo.mark_paid_pending(invoice_id)
        for admin_id in settings.telegram_admin_ids:
            await message.bot.send_message(
                admin_id,
                "⚠️ Оплата принята, но выдача доступа отложена.\n"
                f"Invoice: {invoice_id}\n"
                f"Ошибка: {exc}",
            )
        await message.answer(
            "Оплата подтверждена, но выдача доступа задержана. Мы уже работаем над этим."
        )
        return
    if user and user.subscription_link:
        await _send_access(message, user.subscription_link)
        return
    if user:
        status = await subscription_service.get_status(user.telegram_id)
        if status and status.subscription_link:
            await _send_access(message, status.subscription_link)
        return
    await message.answer(
        "Оплата подтверждена, но ссылка на подписку пока не готова. Напиши в поддержку."
    )

async def _send_access(message: Message, link: str) -> None:
    keyboard = connection_keyboard(link)
    if not keyboard:
        logger.warning("Access link invalid for connection button: %s", link)
        await message.answer("ℹ️ Access link is not ready yet.")
        return
    await message.answer(
        "🛡 DagDev VPN\n"
        "━━━━━━━━━━━━\n"
        "Your VPN is ready.\n"
        "Tap the button below to connect.",
        reply_markup=keyboard,
    )

