from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.keyboards.common import main_menu
from app.services.referral import ReferralService

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message, referral_service: ReferralService) -> None:
    ref_code = message.text.split(" ")[1] if message.text and " " in message.text else None
    if ref_code and ref_code.startswith("ref"):
        referrer_id = int(ref_code.replace("ref", ""))
        has_referrer = await referral_service.has_referrer(message.from_user.id)
        if not has_referrer:
            await referral_service.register_referral(referrer_id, message.from_user.id)
    greeting = (
        "👋 Добро пожаловать!\n\n"
        "Мы даём быстрый и стабильный VPN на базе VLESS/REALITY.\n"
        "Одно касание — и у тебя безопасный интернет без блокировок."
    )
    await message.answer(greeting, reply_markup=main_menu())
