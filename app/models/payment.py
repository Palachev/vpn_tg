from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PaymentInvoice:
    invoice_id: str
    user_id: int
    tariff_code: str
    amount: float
    currency: str
    payment_url: str


@dataclass
class PaymentResult:
    invoice_id: str
    status: str
    amount: float
    currency: str
    paid_at: datetime
