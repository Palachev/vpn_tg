from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.keyboards.common import tariffs_keyboard
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
    text = (
        f"Тариф: {tariff.title}\n"
        f"Цена: ${tariff.price}\n\n"
        "Перейди по ссылке и оплати. После оплаты бот сразу выдаст конфиг."
    )
    await callback.message.answer(text, reply_markup=None)
    await callback.message.answer(f"Ссылка на оплату: {invoice.payment_url}")
    await callback.answer()
