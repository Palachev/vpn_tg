from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import aiohttp


class MarzbanService:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def _request(self, method: str, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.request(method, f"{self.base_url}{path}", json=json, timeout=15) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def create_user(self, username: str, expire_at: datetime, traffic_gb: float | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "username": username,
            "expire": int(expire_at.timestamp()),
        }
        if traffic_gb:
            payload["data_limit"] = int(traffic_gb * 1024**3)
        return await self._request("POST", "/api/user", json=payload)

    async def renew_user(self, username: str, add_days: timedelta) -> dict[str, Any]:
        payload = {"add_days": add_days.days}
        return await self._request("POST", f"/api/user/{username}/renew", json=payload)

    async def get_user(self, username: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/user/{username}")

    async def get_subscription_link(self, username: str) -> str:
        data = await self._request("GET", f"/api/user/{username}/subscription")
        return data.get("url")
