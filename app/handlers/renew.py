from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.keyboards.common import tariffs_keyboard

router = Router()


@router.callback_query(F.data == "renew:start")
async def renew(callback: CallbackQuery) -> None:
    await callback.message.answer("Выбери срок продления:", reply_markup=tariffs_keyboard())
    await callback.answer()
