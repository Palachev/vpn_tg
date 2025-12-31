from __future__ import annotations

from datetime import datetime

from app.db import Database
from app.models.user import User


class UserRepository:
    def __init__(self, db: Database):
        self._db = db

    async def upsert_user(self, user: User) -> None:
        await self._db.execute(
            """
            INSERT INTO users (telegram_id, marzban_username, marzban_uuid, subscription_expires_at, subscription_link, traffic_limit_gb)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                marzban_username=excluded.marzban_username,
                marzban_uuid=excluded.marzban_uuid,
                subscription_expires_at=excluded.subscription_expires_at,
                subscription_link=excluded.subscription_link,
                traffic_limit_gb=excluded.traffic_limit_gb
            """,
            user.telegram_id,
            user.marzban_username,
            user.marzban_uuid,
            user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
            user.subscription_link,
            user.traffic_limit_gb,
        )

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        row = await self._db.fetchone(
            """SELECT telegram_id, marzban_username, marzban_uuid, subscription_expires_at, subscription_link, traffic_limit_gb
            FROM users WHERE telegram_id = ?""",
            telegram_id,
        )
        if not row:
            return None
        subscription_expires_at = (
            datetime.fromisoformat(row[3]) if row[3] else None
        )
        return User(
            telegram_id=row[0],
            marzban_username=row[1],
            marzban_uuid=row[2],
            subscription_expires_at=subscription_expires_at,
            subscription_link=row[4],
            traffic_limit_gb=row[5],
        )

    async def update_subscription(self, telegram_id: int, expires_at: datetime, link: str | None) -> None:
        await self._db.execute(
            """UPDATE users SET subscription_expires_at = ?, subscription_link = ? WHERE telegram_id = ?""",
            expires_at.isoformat(),
            link,
            telegram_id,
        )

    async def count_users(self) -> int:
        row = await self._db.fetchone("SELECT COUNT(*) FROM telegram_users")
        return row[0] if row else 0

    async def count_active_subscriptions(self, now_iso: str) -> int:
        row = await self._db.fetchone(
            "SELECT COUNT(*) FROM users WHERE subscription_expires_at IS NOT NULL AND subscription_expires_at > ?",
            now_iso,
        )
        return row[0] if row else 0

    async def list_telegram_ids(self) -> list[int]:
        rows = await self._db.fetchall("SELECT telegram_id FROM telegram_users")
        return [row[0] for row in rows]

    async def register_telegram_user(self, telegram_id: int) -> None:
        await self._db.execute(
            "INSERT INTO telegram_users (telegram_id) VALUES (?) ON CONFLICT(telegram_id) DO NOTHING",
            telegram_id,
        )
