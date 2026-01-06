from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

router = Router()

FAQ = (
    "Частые ответы:\n"
    "• Не подключается? Переключись на Mobile сервер.\n"
    "• Мобильный интернет: используй профиль gRPC (Mobile).\n"
    "• Сменить сервер: просто выбери другой в клиенте.\n\n"
    "Если что-то пошло не так — напиши в поддержку: @kh4ck"
)


@router.message(F.text == "Помощь")
async def help_message(message: Message) -> None:
    await message.answer(FAQ)


@router.message(F.text == "Оферта / Условия")
async def terms(message: Message) -> None:
    await message.answer(
        "Оплачивая подписку, ты соглашаешься использовать VPN только для легального контента."
        " Оплата не возвращается за уже активированные периоды."
    )
