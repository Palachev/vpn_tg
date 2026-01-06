from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.config import TARIFFS
from app.utils.deeplink import build_happ_deeplink


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="💳 Купить VPN"), KeyboardButton(text="📲 Install VPN")],
            [KeyboardButton(text="📊 Status")],
            [KeyboardButton(text="Пробный период")],
            [KeyboardButton(text="Помощь"), KeyboardButton(text="Оферта / Условия")],
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
        [InlineKeyboardButton(text="🍎 iOS / macOS", callback_data="install:apple")],
        [InlineKeyboardButton(text="🪟 Windows", callback_data="install:windows")],
        [InlineKeyboardButton(text="🤖 Android", callback_data="install:android")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="nav:back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def renew_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="💳 Renew / Buy", callback_data="renew:start")]]
    )


def connection_keyboard(subscription_link: str) -> InlineKeyboardMarkup | None:
    deeplink = build_happ_deeplink(subscription_link)
    if not deeplink:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔑 Connect VPN", url=deeplink)],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="nav:back")],
        ]
    )


def install_keyboard(install_url: str, subscription_link: str | None) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text="⬇️ Install Happ Proxy", url=install_url)]]
    if subscription_link:
        deeplink = build_happ_deeplink(subscription_link)
        if deeplink:
            buttons.append([InlineKeyboardButton(text="🔑 Connect VPN", url=deeplink)])
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="nav:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def status_keyboard(subscription_link: str | None) -> InlineKeyboardMarkup:
    buttons = []
    if subscription_link:
        deeplink = build_happ_deeplink(subscription_link)
        if deeplink:
            buttons.append([InlineKeyboardButton(text="🔑 Connect VPN", url=deeplink)])
    buttons.append([InlineKeyboardButton(text="💳 Renew / Buy", callback_data="renew:start")])
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="nav:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
