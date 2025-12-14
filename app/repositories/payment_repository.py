from __future__ import annotations

from datetime import datetime

from app.db import Database


class PaymentRepository:
    def __init__(self, db: Database):
        self._db = db

    async def create_invoice(self, invoice_id: str, telegram_id: int, tariff_code: str, amount: float, currency: str) -> None:
        await self._db.execute(
            """
            INSERT OR IGNORE INTO payments (invoice_id, telegram_id, tariff_code, amount, currency, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
            """,
            invoice_id,
            telegram_id,
            tariff_code,
            amount,
            currency,
        )

    async def mark_paid(self, invoice_id: str, status: str = "paid") -> None:
        await self._db.execute(
            """UPDATE payments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE invoice_id = ?""",
            status,
            invoice_id,
        )

    async def get_payment(self, invoice_id: str) -> tuple | None:
        return await self._db.fetchone(
            """SELECT invoice_id, telegram_id, tariff_code, amount, currency, status FROM payments WHERE invoice_id = ?""",
            invoice_id,
        )

    async def was_processed(self, invoice_id: str) -> bool:
        row = await self._db.fetchone(
            "SELECT status FROM payments WHERE invoice_id = ? AND status = 'paid'",
            invoice_id,
        )
        return row is not None

    async def complete_or_skip(self, invoice_id: str, status: str) -> bool:
        """Idempotent completion; returns True if marked newly."""
        row = await self._db.fetchone(
            "SELECT status FROM payments WHERE invoice_id = ?",
            invoice_id,
        )
        if row and row[0] == status:
            return False
        await self.mark_paid(invoice_id, status)
        return True

    async def count_successful_payments(self, telegram_id: int) -> int:
        row = await self._db.fetchone(
            "SELECT COUNT(*) FROM payments WHERE telegram_id = ? AND status = 'paid'",
            telegram_id,
        )
        return row[0] if row else 0
