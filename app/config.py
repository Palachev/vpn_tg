from __future__ import annotations

from typing import Dict

from pydantic_settings import BaseSettings
from pydantic import field_validator



TARIFFS: Dict[str, dict] = {
    "m1": {"title": "1 месяц", "days": 30, "price": 5},
    "m3": {"title": "3 месяца", "days": 90, "price": 12},
    "m6": {"title": "6 месяцев", "days": 180, "price": 20},
}


class Settings(BaseSettings):
    telegram_token: str
    telegram_admin_ids: list[int] = []
    marzban_base_url: str
    marzban_api_key: str
    payment_provider_key: str
    payment_public_key: str
    payment_webhook_secret: str
    payment_currency: str = "USD"
    database_path: str = "./bot.db"
    webhook_host: str = "0.0.0.0"
    webhook_path: str = "/payment/webhook"
    base_subscription_days: int = 30
    referral_bonus_days: int = 7

    @field_validator("telegram_admin_ids", mode="before")
    def parse_admin_ids(cls, value: object) -> list[int]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [int(item) for item in value]
        if isinstance(value, str):
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        return [int(value)]

    class Config:
        env_file = ".env"
        env_prefix = ""
