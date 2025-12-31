from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📈 Статистика", callback_data="admin:stats")],
            [InlineKeyboardButton(text="📣 Рассылка", callback_data="admin:broadcast")],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin:refresh")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin:cancel")],
        ]
    )
