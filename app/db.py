from __future__ import annotations

import asyncio
from typing import Any

import aiosqlite


class Database:
    def __init__(self, path: str):
        self._path = path
        self._lock = asyncio.Lock()
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self._path)
        await self._conn.execute("PRAGMA foreign_keys = ON;")
        await self._create_schema()

    async def _create_schema(self) -> None:
        assert self._conn is not None
        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                marzban_username TEXT NOT NULL UNIQUE,
                marzban_uuid TEXT NOT NULL UNIQUE,
                subscription_expires_at TEXT,
                subscription_link TEXT,
                traffic_limit_gb REAL,
                trial_used INTEGER DEFAULT 0,
                referrer_telegram_id INTEGER,
                referral_bonus_applied INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS telegram_users (
                telegram_id INTEGER PRIMARY KEY,
                trial_used INTEGER DEFAULT 0,
                referrer_telegram_id INTEGER,
                referral_bonus_applied INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS payments (
                invoice_id TEXT PRIMARY KEY,
                telegram_id INTEGER NOT NULL,
                tariff_code TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(invoice_id, status)
            );

            CREATE TABLE IF NOT EXISTS referrals (
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(referrer_id) REFERENCES users(telegram_id)
            );

            CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(telegram_id);
            CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);
            """
        )
        await self._conn.execute(
            """
            INSERT OR IGNORE INTO telegram_users (telegram_id)
            SELECT telegram_id FROM users
            """
        )
        await self._ensure_user_columns()
        await self._conn.commit()

    async def _ensure_user_columns(self) -> None:
        assert self._conn is not None
        await self._ensure_columns(
            "users",
            {
                "trial_used": "INTEGER DEFAULT 0",
                "referrer_telegram_id": "INTEGER",
                "referral_bonus_applied": "INTEGER DEFAULT 0",
            },
        )
        await self._ensure_columns(
            "telegram_users",
            {
                "trial_used": "INTEGER DEFAULT 0",
                "referrer_telegram_id": "INTEGER",
                "referral_bonus_applied": "INTEGER DEFAULT 0",
            },
        )

    async def _ensure_columns(self, table: str, columns: dict[str, str]) -> None:
        assert self._conn is not None
        cursor = await self._conn.execute(f"PRAGMA table_info({table});")
        existing = {row[1] for row in await cursor.fetchall()}
        await cursor.close()
        for name, definition in columns.items():
            if name not in existing:
                await self._conn.execute(
                    f"ALTER TABLE {table} ADD COLUMN {name} {definition}"
                )

    async def execute(self, query: str, *args: Any) -> None:
        assert self._conn is not None
        async with self._lock:
            await self._conn.execute(query, args)
            await self._conn.commit()

    async def execute_with_rowcount(self, query: str, *args: Any) -> int:
        assert self._conn is not None
        async with self._lock:
            cursor = await self._conn.execute(query, args)
            await self._conn.commit()
            rowcount = cursor.rowcount
            await cursor.close()
            return rowcount

    async def fetchone(self, query: str, *args: Any) -> Any:
        assert self._conn is not None
        async with self._lock:
            cursor = await self._conn.execute(query, args)
            row = await cursor.fetchone()
            await cursor.close()
            return row

    async def fetchall(self, query: str, *args: Any) -> list[Any]:
        assert self._conn is not None
        async with self._lock:
            cursor = await self._conn.execute(query, args)
            rows = await cursor.fetchall()
            await cursor.close()
            return rows

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
