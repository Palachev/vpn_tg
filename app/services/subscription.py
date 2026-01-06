from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import asyncio
import logging
import math
from urllib.parse import urljoin, urlparse
from typing import Optional

import aiohttp

from app.config import TARIFFS, Settings
from app.models.status import SubscriptionSnapshot
from app.models.tariff import DEFAULT_TRAFFIC_LIMIT_GB, Tariff
from app.models.user import User
from app.repositories.payment_repository import PaymentRepository
from app.repositories.user_repository import UserRepository
from app.services.marzban import MarzbanService


class SubscriptionService:
    TRIAL_DURATION = timedelta(days=1)
    TRIAL_TRAFFIC_LIMIT_GB = 5.0

    def __init__(
        self,
        settings: Settings,
        user_repo: UserRepository,
        payment_repo: PaymentRepository,
        marzban: MarzbanService,
    ):
        self.settings = settings
        self.user_repo = user_repo
        self.payment_repo = payment_repo
        self.marzban = marzban
        self._logger = logging.getLogger(__name__)
        self._locks: dict[int, asyncio.Lock] = {}

    @asynccontextmanager
    async def _user_lock(self, telegram_id: int) -> object:
        lock = self._locks.setdefault(telegram_id, asyncio.Lock())
        async with lock:
            yield

    def get_tariff(self, code: str) -> Tariff:
        plan = TARIFFS[code]
        return Tariff(
            code=code,
            title=plan["title"],
            price=plan["price"],
            duration=timedelta(days=plan["days"]),
        )

    async def provision_user(
        self,
        telegram_id: int,
        tariff: Tariff,
        referral_bonus: timedelta | None = None,
        traffic_limit_gb: float | None = None,
    ) -> User:
        existing = await self.user_repo.get_by_telegram_id(telegram_id)
        trial_used_meta, referrer_meta, bonus_applied_meta = await self.user_repo.get_user_meta(telegram_id)
        bonus = referral_bonus or timedelta()
        now = datetime.utcnow()
        username = existing.marzban_username if existing else f"tg_{telegram_id}"
        created = False
        marzban_user: dict[str, object] | None = None

        try:
            marzban_user = await self.marzban.get_user(username)
            self._logger.info(
                "Marzban user found for provisioning: telegram_id=%s username=%s",
                telegram_id,
                username,
            )
        except aiohttp.ClientResponseError as exc:
            if exc.status == 404:
                marzban_user = None
            elif exc.status == 500:
                self._logger.warning(
                    "Marzban get_user returned 500, retrying: telegram_id=%s username=%s",
                    telegram_id,
                    username,
                )
                try:
                    marzban_user = await self.marzban.get_user(username)
                except aiohttp.ClientResponseError as retry_exc:
                    if retry_exc.status == 404:
                        marzban_user = None
                    elif retry_exc.status == 500:
                        self._logger.error(
                            "Marzban get_user repeated 500, aborting provisioning: telegram_id=%s username=%s",
                            telegram_id,
                            username,
                        )
                        raise
                    else:
                        self._logger.exception(
                            "Marzban get_user failed after retry: telegram_id=%s username=%s status=%s",
                            telegram_id,
                            username,
                            retry_exc.status,
                        )
                        raise
            else:
                self._logger.exception(
                    "Marzban get_user failed: telegram_id=%s username=%s status=%s",
                    telegram_id,
                    username,
                    exc.status,
                )
                raise

        current_expires_at = (
            self._extract_expire(marzban_user) if marzban_user else None
        ) or (existing.subscription_expires_at if existing else None)
        if not current_expires_at:
            current_expires_at = now
        effective_base = max(current_expires_at, now)
        target_expires_at = effective_base + tariff.duration + bonus

        if marzban_user is None:
            try:
                marzban_user = await self.marzban.create_user(
                    username,
                    target_expires_at,
                    traffic_limit_gb or DEFAULT_TRAFFIC_LIMIT_GB,
                    proxy=self.settings.marzban_proxy or None,
                    flow=self.settings.marzban_flow or None,
                    inbounds=self.settings.marzban_inbounds or None,
                )
                created = True
                self._logger.info(
                    "Marzban user created: telegram_id=%s username=%s",
                    telegram_id,
                    username,
                )
            except aiohttp.ClientResponseError as exc:
                if exc.status in {409, 422}:
                    self._logger.warning(
                        "Marzban user already exists on create, syncing: telegram_id=%s username=%s",
                        telegram_id,
                        username,
                    )
                    marzban_user = await self.marzban.get_user(username)
                else:
                    self._logger.exception(
                        "Marzban create_user failed: telegram_id=%s username=%s status=%s",
                        telegram_id,
                        username,
                        exc.status,
                    )
                    raise

        if not created:
            add_days = self._calculate_add_days(current_expires_at, target_expires_at)
            if add_days > 0:
                await self.marzban.update_user_expire(username, target_expires_at)
                self._logger.info(
                    "Marzban user renewed: telegram_id=%s username=%s add_days=%s new_expire=%s",
                    telegram_id,
                    username,
                    add_days,
                    target_expires_at.isoformat(),
                )
            else:
                self._logger.info(
                    "Marzban renewal skipped (no additional days): telegram_id=%s username=%s",
                    telegram_id,
                    username,
                )

        existing_link = existing.subscription_link if existing else None
        link = existing_link or await self._fetch_subscription_link(username, marzban_user)
        if existing_link:
            self._logger.info(
                "Using existing subscription link for user: telegram_id=%s username=%s",
                telegram_id,
                username,
            )
        marzban_uuid = ""
        if marzban_user:
            marzban_uuid = str(marzban_user.get("uuid") or "")
        if not marzban_uuid:
            marzban_uuid = existing.marzban_uuid if existing else username

        user = User(
            telegram_id=telegram_id,
            marzban_username=username,
            marzban_uuid=marzban_uuid or (existing.marzban_uuid if existing else ""),
            subscription_expires_at=target_expires_at,
            subscription_link=existing_link or link or (existing.subscription_link if existing else None),
            traffic_limit_gb=existing.traffic_limit_gb if existing else (traffic_limit_gb or DEFAULT_TRAFFIC_LIMIT_GB),
            trial_used=existing.trial_used if existing else trial_used_meta,
            referrer_telegram_id=existing.referrer_telegram_id if existing else referrer_meta,
            referral_bonus_applied=existing.referral_bonus_applied if existing else bonus_applied_meta,
        )
        await self.user_repo.upsert_user(user)
        return user

    async def process_payment_success(self, invoice_id: str) -> Optional[User]:
        payment_row = await self.payment_repo.get_payment(invoice_id)
        if not payment_row:
            return None
        invoice_id, telegram_id, tariff_code, amount, currency, status = payment_row
        marked = await self.payment_repo.complete_or_skip(invoice_id)
        if not marked:
            return await self.user_repo.get_by_telegram_id(telegram_id)
        tariff = self.get_tariff(tariff_code)
        async with self._user_lock(telegram_id):
            user = await self.provision_user(telegram_id, tariff)
            await self._apply_referral_bonus(telegram_id)
            return user

    async def provision_trial(self, telegram_id: int) -> User:
        tariff = Tariff(
            code="trial",
            title="Пробный период",
            price=0.0,
            duration=self.TRIAL_DURATION,
        )
        async with self._user_lock(telegram_id):
            return await self.provision_user(
                telegram_id,
                tariff,
                traffic_limit_gb=self.TRIAL_TRAFFIC_LIMIT_GB,
            )

    async def get_status(self, telegram_id: int) -> User | None:
        snapshot = await self.get_status_snapshot(telegram_id)
        return snapshot.user if snapshot else None

    async def get_status_snapshot(self, telegram_id: int) -> SubscriptionSnapshot | None:
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            return None
        username = user.marzban_username or f"tg_{telegram_id}"
        try:
            marzban_user = await self.marzban.get_user(username)
            expires_at = self._extract_expire(marzban_user) or user.subscription_expires_at
            link = user.subscription_link or await self._fetch_subscription_link(username, marzban_user)
            used_gb, limit_gb = self._extract_traffic(marzban_user)
            traffic_limit = limit_gb or user.traffic_limit_gb
            if (expires_at != user.subscription_expires_at) or (
                not user.subscription_link and link and link != user.subscription_link
            ):
                await self.user_repo.update_subscription(
                    telegram_id,
                    expires_at or user.subscription_expires_at,
                    link or user.subscription_link,
                )
            updated_user = User(
                telegram_id=user.telegram_id,
                marzban_username=username,
                marzban_uuid=user.marzban_uuid,
                subscription_expires_at=expires_at,
                subscription_link=link or user.subscription_link,
                traffic_limit_gb=traffic_limit,
                is_stale=False,
                trial_used=user.trial_used,
                referrer_telegram_id=user.referrer_telegram_id,
                referral_bonus_applied=user.referral_bonus_applied,
            )
            return SubscriptionSnapshot(
                user=updated_user,
                traffic_used_gb=used_gb,
                traffic_limit_gb=traffic_limit,
                server_label="Auto",
                is_stale=False,
            )
        except aiohttp.ClientResponseError as exc:
            self._logger.warning(
                "Marzban status sync failed, returning local data: telegram_id=%s username=%s status=%s",
                telegram_id,
                username,
                exc.status,
            )
            stale_user = User(
                telegram_id=user.telegram_id,
                marzban_username=username,
                marzban_uuid=user.marzban_uuid,
                subscription_expires_at=user.subscription_expires_at,
                subscription_link=user.subscription_link,
                traffic_limit_gb=user.traffic_limit_gb,
                is_stale=True,
                trial_used=user.trial_used,
                referrer_telegram_id=user.referrer_telegram_id,
                referral_bonus_applied=user.referral_bonus_applied,
            )
            return SubscriptionSnapshot(
                user=stale_user,
                traffic_used_gb=None,
                traffic_limit_gb=user.traffic_limit_gb,
                server_label="Auto",
                is_stale=True,
            )

    def _extract_expire(self, marzban_user: dict[str, object] | None) -> datetime | None:
        if not marzban_user:
            return None
        expire = marzban_user.get("expire")
        if isinstance(expire, (int, float)) and expire > 0:
            return datetime.utcfromtimestamp(expire)
        if isinstance(expire, str):
            try:
                return datetime.fromisoformat(expire)
            except ValueError:
                return None
        return None

    def _calculate_add_days(self, current_expires_at: datetime, new_expires_at: datetime) -> int:
        delta_seconds = (new_expires_at - current_expires_at).total_seconds()
        if delta_seconds <= 0:
            return 0
        return int(math.ceil(delta_seconds / 86400))

    def _extract_traffic(self, marzban_user: dict[str, object] | None) -> tuple[float | None, float | None]:
        if not marzban_user:
            return None, None
        limit_bytes = self._get_numeric_value(marzban_user, ["data_limit", "data_limit_bytes"])
        used_bytes = self._get_numeric_value(marzban_user, ["used_traffic", "data_used", "used_data", "traffic_used"])
        limit_gb = self._bytes_to_gb(limit_bytes) if limit_bytes else None
        used_gb = self._bytes_to_gb(used_bytes) if used_bytes else None
        return used_gb, limit_gb

    def _get_numeric_value(self, payload: dict[str, object], keys: list[str]) -> float | None:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str) and value.isdigit():
                return float(value)
        return None

    def _bytes_to_gb(self, value: float) -> float:
        return value / 1024**3

    async def _fetch_subscription_link(
        self,
        username: str,
        marzban_user: dict[str, object] | None,
    ) -> str:
        link = ""
        if not link and marzban_user:
            link = (
                str(marzban_user.get("subscription_url") or "")
                or str(marzban_user.get("subscription_link") or "")
                or str(marzban_user.get("link") or "")
            )
        if not link and marzban_user:
            links = marzban_user.get("links")
            if isinstance(links, list):
                link = "\n".join(str(item) for item in links if item)
            elif isinstance(links, str):
                link = links
        if not link:
            base_url = self.settings.public_base_url or self.settings.marzban_base_url
            link = urljoin(base_url.rstrip("/") + "/", f"sub/{username}")
        normalized = self._ensure_absolute_link(link)
        if not normalized:
            self._logger.warning("Subscription link missing/invalid: username=%s", username)
        return normalized

    def _ensure_absolute_link(self, link: str) -> str:
        if not link:
            return ""
        parsed = urlparse(link)
        if parsed.scheme and parsed.netloc:
            return link
        if link.startswith("/"):
            base_url = self.settings.public_base_url or self.settings.marzban_base_url
            return urljoin(base_url.rstrip("/") + "/", link.lstrip("/"))
        return ""

    async def _apply_referral_bonus(self, invitee_id: int) -> None:
        referrer_id = await self.user_repo.get_referrer_id(invitee_id)
        if not referrer_id or referrer_id == invitee_id:
            return
        marked = await self.user_repo.try_mark_referral_bonus_applied(invitee_id)
        if not marked:
            return
        bonus_days = timedelta(days=self.settings.referral_bonus_days)
        bonus_tariff = Tariff(
            code="referral_bonus",
            title="Referral bonus",
            price=0.0,
            duration=timedelta(),
        )
        try:
            async with self._user_lock(referrer_id):
                await self.provision_user(referrer_id, bonus_tariff, referral_bonus=bonus_days)
            self._logger.info(
                "Referral bonus applied: invitee=%s referrer=%s days=%s",
                invitee_id,
                referrer_id,
                self.settings.referral_bonus_days,
            )
        except Exception:
            self._logger.exception(
                "Failed to apply referral bonus: invitee=%s referrer=%s",
                invitee_id,
                referrer_id,
            )
