from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from app.config import TARIFFS, Settings
from app.models.tariff import DEFAULT_TRAFFIC_LIMIT_GB, Tariff
from app.models.user import User
from app.repositories.payment_repository import PaymentRepository
from app.repositories.user_repository import UserRepository
from app.services.marzban import MarzbanService


class SubscriptionService:
    def __init__(
        self,
        settings: Settings,
        user_repo: UserRepository,
        payment_repo: PaymentRepository,
        marzban: MarzbanService,
    ):
        self.settings = settings
        self.user_repo = user_repo
        self.payment_repo = payment_repo
        self.marzban = marzban

    def get_tariff(self, code: str) -> Tariff:
        plan = TARIFFS[code]
        return Tariff(
            code=code,
            title=plan["title"],
            price=plan["price"],
            duration=timedelta(days=plan["days"]),
        )

    async def provision_user(self, telegram_id: int, tariff: Tariff, referral_bonus: timedelta | None = None) -> User:
        existing = await self.user_repo.get_by_telegram_id(telegram_id)
        bonus = referral_bonus or timedelta()
        expires_at = datetime.utcnow() + tariff.duration + bonus
        username = existing.marzban_username if existing else f"tg{telegram_id}"
        if existing:
            await self.marzban.renew_user(username, tariff.duration + bonus)
            link = await self.marzban.get_subscription_link(username)
            await self.user_repo.update_subscription(telegram_id, expires_at, link)
            return User(
                telegram_id=telegram_id,
                marzban_username=username,
                marzban_uuid=existing.marzban_uuid,
                subscription_expires_at=expires_at,
                subscription_link=link,
                traffic_limit_gb=existing.traffic_limit_gb,
            )
        created = await self.marzban.create_user(username, expires_at, DEFAULT_TRAFFIC_LIMIT_GB)
        link = await self.marzban.get_subscription_link(username)
        user = User(
            telegram_id=telegram_id,
            marzban_username=username,
            marzban_uuid=created.get("uuid", ""),
            subscription_expires_at=expires_at,
            subscription_link=link,
            traffic_limit_gb=DEFAULT_TRAFFIC_LIMIT_GB,
        )
        await self.user_repo.upsert_user(user)
        return user

    async def process_payment_success(self, invoice_id: str) -> Optional[User]:
        payment_row = await self.payment_repo.get_payment(invoice_id)
        if not payment_row:
            return None
        invoice_id, telegram_id, tariff_code, amount, currency, status = payment_row
        if status == "paid":
            return await self.user_repo.get_by_telegram_id(telegram_id)
        marked = await self.payment_repo.complete_or_skip(invoice_id, "paid")
        if not marked:
            return await self.user_repo.get_by_telegram_id(telegram_id)
        tariff = self.get_tariff(tariff_code)
        user = await self.provision_user(telegram_id, tariff)
        return user

    async def get_status(self, telegram_id: int) -> User | None:
        return await self.user_repo.get_by_telegram_id(telegram_id)
