from __future__ import annotations

from typing import Dict

from pydantic_settings import BaseSettings
from pydantic import field_validator



TARIFFS: Dict[str, dict] = {
    "m1": {"title": "1 месяц", "days": 30, "price": 1},
    "m3": {"title": "3 месяца", "days": 90, "price": 2},
    "m6": {"title": "6 месяцев", "days": 180, "price": 4},
    "m12": {"title": "12 месяцев", "days": 365, "price": 8},
}


class Settings(BaseSettings):
    telegram_token: str
    telegram_admin_ids: list[int] = []
    marzban_base_url: str
    public_base_url: str | None = None
    marzban_api_key: str
    marzban_proxy: str = "vless"
    marzban_flow: str = "xtls-rprx-vision"
    marzban_inbounds: list[str] = ["VLESS TCP REALITY"]
    payment_provider_key: str
    payment_public_key: str
    payment_webhook_secret: str
    payment_currency: str = "XTR"
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

    @field_validator("marzban_inbounds", mode="before")
    def parse_marzban_inbounds(cls, value: object) -> list[str]:
        if value is None or value == "":
            return ["VLESS TCP REALITY"]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return [str(value)]

    @field_validator("public_base_url", mode="before")
    def parse_public_base_url(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip() or None
        return str(value)

    class Config:
        env_file = ".env"
        env_prefix = ""
