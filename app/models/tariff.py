from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass
class Tariff:
    code: str
    title: str
    price: float
    duration: timedelta

    def __post_init__(self) -> None:
        if isinstance(self.duration, int):
            self.duration = timedelta(days=self.duration)


DEFAULT_TRAFFIC_LIMIT_GB = 300