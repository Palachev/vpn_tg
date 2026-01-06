from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.keyboards.common import install_keyboard, platform_keyboard
from app.services.subscription import SubscriptionService

router = Router()

FALLBACK_INSTALL_URL = "https://happ.pro"


@router.message(F.text == "📲 Install VPN")
async def pick_platform(message: Message) -> None:
    await message.answer("🛡 DagDev VPN\n━━━━━━━━━━━━\nSelect your OS.", reply_markup=platform_keyboard())


@router.callback_query(F.data.startswith("install:"))
async def send_guide(
    callback: CallbackQuery,
    settings: Settings,
    subscription_service: SubscriptionService,
) -> None:
    platform = callback.data.split(":", maxsplit=1)[1]
    install_url_map = {
        "apple": settings.happ_apple_url,
        "windows": settings.happ_windows_url,
        "android": settings.happ_android_url,
    }
    install_url = install_url_map.get(platform) or FALLBACK_INSTALL_URL
    user = await subscription_service.get_status(callback.from_user.id)
    has_active_subscription = bool(
        user
        and user.subscription_expires_at
        and user.subscription_expires_at > datetime.utcnow()
    )
    text = "🛡 DagDev VPN\n━━━━━━━━━━━━\nInstall Happ Proxy and connect your VPN."
    if not has_active_subscription:
        text = f"{text}\n\nℹ️ Buy VPN to connect."
    subscription_link = user.subscription_link if has_active_subscription and user else None
    await callback.message.answer(text, reply_markup=install_keyboard(install_url, subscription_link))
    await callback.answer()
