from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.keyboards.common import platform_keyboard

router = Router()

PLATFORM_GUIDES = {
    "android": {
        "app": "v2rayNG",
        "url": "https://play.google.com/store/apps/details?id=com.v2ray.ang",
        "steps": [
            "Скачай v2rayNG из Google Play",
            "Нажми + и выбери 'Добавить из ссылки'",
            "Вставь подписку, которую пришлёт бот",
            "Выбери сервер Fast или Mobile и нажми Connect",
        ],
    },
    "ios": {
        "app": "Streisand",
        "url": "https://apps.apple.com/app/streisand/id6450534064",
        "steps": [
            "Скачай Streisand в App Store",
            "Нажми 'Add from link'",
            "Вставь ссылку-подписку",
            "Нажми на понравившийся сервер",
        ],
    },
    "windows": {
        "app": "v2rayN",
        "url": "https://github.com/2dust/v2rayN/releases",
        "steps": [
            "Скачай архив v2rayN, распакуй и запусти v2rayN.exe",
            "Добавь подписку через кнопку '订阅' -> '订阅设置'",
            "Вставь ссылку и обнови список серверов",
            "Двойной клик по серверу для подключения",
        ],
    },
    "macos": {
        "app": "FoXray",
        "url": "https://apps.apple.com/app/foxray/id6448898396",
        "steps": [
            "Установи FoXray из App Store",
            "Нажми + и выбери 'Import from URL'",
            "Вставь ссылку-подписку",
            "Выбери сервер Fast, если не работает — Mobile",
        ],
    },
}


@router.message(F.text == "🔑 Установить VPN")
async def pick_platform(message: Message) -> None:
    await message.answer("Выбери платформу, пошаговые инструкции ниже:", reply_markup=platform_keyboard())


@router.callback_query(F.data.startswith("install:"))
async def send_guide(callback: CallbackQuery) -> None:
    platform = callback.data.split(":", maxsplit=1)[1]
    guide = PLATFORM_GUIDES[platform]
    steps = "\n".join([f"{idx+1}. {step}" for idx, step in enumerate(guide["steps"] )])
    text = (
        f"{guide['app']}\n{guide['url']}\n\n"
        "Как подключить:\n"
        f"{steps}\n\n"
        "После оплаты бот пришлёт твою персональную ссылку подписки."
    )
    await callback.message.answer(text)
    await callback.answer()
