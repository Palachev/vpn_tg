from __future__ import annotations

from datetime import timedelta

from app.config import Settings
from app.repositories.referral_repository import ReferralRepository


class ReferralService:
    def __init__(self, settings: Settings, repository: ReferralRepository):
        self.settings = settings
        self.repository = repository

    def generate_ref_link(self, bot_username: str, user_id: int) -> str:
        return f"https://t.me/{bot_username}?start=ref{user_id}"

    async def register_referral(self, referrer_id: int, referred_id: int) -> bool:
        if referrer_id == referred_id:
            return False
        return await self.repository.add_referral(referrer_id, referred_id)

    async def bonus_days(self, referrer_id: int) -> timedelta:
        count = await self.repository.count_referrals(referrer_id)
        return timedelta(days=count * self.settings.referral_bonus_days)

    async def has_referrer(self, referred_id: int) -> bool:
        return await self.repository.has_referrer(referred_id)
