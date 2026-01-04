from __future__ import annotations

from datetime import timedelta

from app.config import Settings
from app.repositories.referral_repository import ReferralRepository
from app.repositories.user_repository import UserRepository


class ReferralService:
    def __init__(self, settings: Settings, repository: ReferralRepository, user_repo: UserRepository):
        self.settings = settings
        self.repository = repository
        self.user_repo = user_repo

    def generate_ref_link(self, bot_username: str, user_id: int) -> str:
        return f"https://t.me/{bot_username}?start={user_id}"

    async def register_referral(self, referrer_id: int, referred_id: int) -> bool:
        if referrer_id == referred_id:
            return False
        was_set = await self.user_repo.set_referrer(referred_id, referrer_id)
        if was_set:
            await self.repository.add_referral(referrer_id, referred_id)
        return was_set

    async def bonus_days(self, referrer_id: int) -> timedelta:
        count = await self.repository.count_referrals(referrer_id)
        return timedelta(days=count * self.settings.referral_bonus_days)

    async def has_referrer(self, referred_id: int) -> bool:
        return (await self.user_repo.get_referrer_id(referred_id)) is not None
