from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from app.keyboards.common import main_menu

router = Router()


@router.message(F.text == "Пригласить друга")
async def share_referral(message: Message) -> None:
    await message.answer("Выбери действие.", reply_markup=main_menu())
