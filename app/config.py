from __future__ import annotations

from datetime import timedelta
from typing import Dict, List

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    telegram_token: str = Field(..., env="TELEGRAM_TOKEN")
    telegram_admin_ids: List[int] = Field(default_factory=list, env="TELEGRAM_ADMIN_IDS")

    marzban_base_url: str = Field(..., env="MARZBAN_BASE_URL")
    marzban_api_key: str = Field(..., env="MARZBAN_API_KEY")

    payment_provider_key: str = Field("", env="PAYMENT_PROVIDER_KEY")
    payment_public_key: str = Field("", env="PAYMENT_PUBLIC_KEY")
    payment_webhook_secret: str = Field(..., env="PAYMENT_WEBHOOK_SECRET")
    payment_currency: str = Field("USD", env="PAYMENT_CURRENCY")

    database_path: str = Field("./bot.db", env="DATABASE_PATH")

    webhook_host: str = Field("0.0.0.0", env="WEBHOOK_HOST")
    webhook_port: int = Field(8080, env="WEBHOOK_PORT")
    webhook_path: str = Field("/payment/webhook", env="WEBHOOK_PATH")

    base_subscription_days: int = Field(30, env="BASE_SUBSCRIPTION_DAYS")
    referral_bonus_days: int = Field(7, env="REFERRAL_BONUS_DAYS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @validator("telegram_admin_ids", pre=True)
    def split_admins(cls, v: str | List[int]):
        if isinstance(v, list):
            return v
        if not v:
            return []
        return [int(item) for item in v.split(",") if item]


# Тарифы выводятся в меню и используются для расчёта длительности/стоимости.
TARIFFS: Dict[str, dict] = {
    "1m": {"title": "1 месяц", "price": 6.9, "days": 30},
    "3m": {"title": "3 месяца", "price": 17.9, "days": 90},
    "6m": {"title": "6 месяцев", "price": 29.9, "days": 180},
}


def tariff_duration(days: int) -> timedelta:
    return timedelta(days=days)
