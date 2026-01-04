from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.config import TARIFFS


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="💳 Купить VPN"), KeyboardButton(text="🔑 Установить VPN")],
            [KeyboardButton(text="📊 Статус"), KeyboardButton(text="🎁 Пригласить друга")],
            [KeyboardButton(text="🆓 Пробный период")],
            [KeyboardButton(text="🆘 Помощь"), KeyboardButton(text="📄 Оферта / Условия")],
        ],
    )


def tariffs_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=f"{plan['title']} — {plan['price']}⭐", callback_data=f"buy:{code}")]
        for code, plan in TARIFFS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def platform_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📱 Android", callback_data="install:android")],
        [InlineKeyboardButton(text="🍎 iOS", callback_data="install:ios")],
        [InlineKeyboardButton(text="💻 Windows", callback_data="install:windows")],
        [InlineKeyboardButton(text="💻 macOS", callback_data="install:macos")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def renew_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Продлить", callback_data="renew:start")]]
    )
