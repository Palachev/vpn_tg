from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass
class Tariff:
    code: str
    title: str
    price: float
    duration: timedelta


DEFAULT_TRAFFIC_LIMIT_GB = 300
