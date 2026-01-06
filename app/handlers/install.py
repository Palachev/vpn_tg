from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.keyboards.common import install_actions_keyboard, platform_keyboard, renew_keyboard
from app.services.subscription import SubscriptionService

router = Router()

PLATFORM_URLS = {
    "apple": "happ_apple_url",
    "windows": "happ_windows_url",
    "android": "happ_android_url",
}


@router.message(F.text == "🔑 Установить VPN")
async def pick_platform(message: Message) -> None:
    await message.answer("Выберите устройство.", reply_markup=platform_keyboard())


@router.callback_query(F.data == "install:back")
async def install_back(callback: CallbackQuery) -> None:
    await callback.message.answer("Выберите устройство.", reply_markup=platform_keyboard())
    await callback.answer()


@router.callback_query(F.data.in_({"install:apple", "install:windows", "install:android"}))
async def send_install(
    callback: CallbackQuery,
    subscription_service: SubscriptionService,
    settings: Settings,
) -> None:
    platform = callback.data.split(":", maxsplit=1)[1]
    setting_key = PLATFORM_URLS.get(platform)
    if not setting_key:
        await callback.answer()
        return
    user = await subscription_service.get_status(callback.from_user.id)
    if not user or not user.subscription_link:
        await callback.message.answer(
            "ℹ️ Сначала оформите подписку.",
            reply_markup=renew_keyboard(),
        )
        await callback.answer()
        return
    install_url = getattr(settings, setting_key)
    keyboard = install_actions_keyboard(
        install_url=install_url,
        subscription_link=user.subscription_link,
        profile_name="DagDev VPN",
    )
    if not keyboard:
        await callback.message.answer("ℹ️ Access link is not ready yet.")
        await callback.answer()
        return
    text = (
        "🛡 DagDev VPN\n"
        "━━━━━━━━━━━━\n"
        "Install Happ Proxy and then connect your VPN."
    )
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()
