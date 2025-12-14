from __future__ import annotations

from app.db import Database


class ReferralRepository:
    def __init__(self, db: Database):
        self._db = db

    async def add_referral(self, referrer_id: int, referred_id: int) -> bool:
        try:
            await self._db.execute(
                "INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)",
                referrer_id,
                referred_id,
            )
            return True
        except Exception:
            return False

    async def count_referrals(self, referrer_id: int) -> int:
        row = await self._db.fetchone(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id = ?",
            referrer_id,
        )
        return row[0] if row else 0

    async def has_referrer(self, referred_id: int) -> bool:
        row = await self._db.fetchone(
            "SELECT 1 FROM referrals WHERE referred_id = ?",
            referred_id,
        )
        return row is not None
