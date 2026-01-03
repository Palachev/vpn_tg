from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    telegram_id: int
    marzban_username: str
    marzban_uuid: str
    subscription_expires_at: datetime | None
    subscription_link: str | None
    traffic_limit_gb: float | None
    is_stale: bool = False
