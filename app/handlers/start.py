from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.keyboards.common import main_menu
from app.repositories.user_repository import UserRepository
from app.services.referral import ReferralService

router = Router()


@router.message(CommandStart())
async def handle_start(
    message: Message,
    referral_service: ReferralService,
    user_repo: UserRepository,
) -> None:
    await user_repo.register_telegram_user(message.from_user.id)
    ref_code = message.text.split(" ")[1] if message.text and " " in message.text else None
    if ref_code:
        ref_value = ref_code.replace("ref", "")
        if ref_value.isdigit():
            referrer_id = int(ref_value)
            await referral_service.register_referral(referrer_id, message.from_user.id)
<<<<<<< HEAD
    await message.answer("🛡 DagDev VPN\n━━━━━━━━━━━━\nВыбери действие ниже.", reply_markup=main_menu())
=======
    greeting = (
        "👋 Добро пожаловать!\n\n"
        "Мы даём быстрый и стабильный VPN на базе VLESS/REALITY.\n"
        "Одно касание — и у тебя безопасный интернет без блокировок.\n"
	"Пока бот находится в разработке это тестовый запуск"
    )
    await message.answer(greeting, reply_markup=main_menu())
>>>>>>> e2229bf (Fix bug)
