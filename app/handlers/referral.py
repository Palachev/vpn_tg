from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from app.services.referral import ReferralService

router = Router()


@router.message(F.text == "🎁 Пригласить друга")
async def share_referral(message: Message, referral_service: ReferralService, bot_username: str) -> None:
    link = referral_service.generate_ref_link(bot_username, message.from_user.id)
    text = (
        "Приводи друзей и получай +7 дней к подписке.\n\n"
        f"Твоя ссылка: {link}\n"
        "За каждого друга — +7 дней к сроку. Бонусы суммируются автоматически."
    )
    await message.answer(text)
