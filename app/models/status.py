from __future__ import annotations

from dataclasses import dataclass

from app.models.user import User


@dataclass
class SubscriptionSnapshot:
    user: User
    traffic_used_gb: float | None
    traffic_limit_gb: float | None
    server_label: str | None
    is_stale: bool
