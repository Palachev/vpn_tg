from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime
from typing import Any

from app.config import Settings
from app.models.payment import PaymentInvoice, PaymentResult
from app.repositories.payment_repository import PaymentRepository


class PaymentService:
    def __init__(self, settings: Settings, payment_repo: PaymentRepository):
        self.settings = settings
        self.payment_repo = payment_repo

    async def create_invoice(self, user_id: int, tariff_code: str, amount: float) -> PaymentInvoice:
        invoice_id = self._generate_invoice_id(user_id, tariff_code)
        await self.payment_repo.create_invoice(invoice_id, user_id, tariff_code, amount, self.settings.payment_currency)
        payment_url = f"https://pay.example.com/checkout?invoice={invoice_id}"  # replace with real provider
        return PaymentInvoice(
            invoice_id=invoice_id,
            user_id=user_id,
            tariff_code=tariff_code,
            amount=amount,
            currency=self.settings.payment_currency,
            payment_url=payment_url,
        )

    async def verify_webhook(self, payload: str, signature: str) -> PaymentResult | None:
        secret = self.settings.payment_webhook_secret.encode()
        expected_signature = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_signature, signature):
            return None
        data: dict[str, Any] = json.loads(payload)
        if data.get("status") != "paid":
            return None
        return PaymentResult(
            invoice_id=data["invoice_id"],
            status=data["status"],
            amount=float(data["amount"]),
            currency=data["currency"],
            paid_at=datetime.fromisoformat(data["paid_at"]),
        )

    def _generate_invoice_id(self, user_id: int, tariff_code: str) -> str:
        raw = f"{user_id}-{tariff_code}-{datetime.utcnow().timestamp()}"
        return hashlib.sha1(raw.encode()).hexdigest()
