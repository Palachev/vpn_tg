from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from app.keyboards.common import tariffs_keyboard
from app.repositories.payment_repository import PaymentRepository
from app.services.payments import PaymentService
from app.services.subscription import SubscriptionService

router = Router()


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
    user = await subscription_service.process_payment_success(invoice_id)
    if user and user.subscription_link:
        safe_link = html.escape(user.subscription_link)
        await message.answer(
            "✅ Оплата подтверждена!\n\n"
            "Вот твоя ссылка для подключения:\n"
            f"<code>{safe_link}</code>\n\n"
            "Инструкция по установке доступна в меню «📱 Установка»."
        )
        return
    await message.answer(
        "Оплата подтверждена, но ссылка на подписку пока не готова. Напиши в поддержку."
    )
