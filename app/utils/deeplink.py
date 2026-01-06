from __future__ import annotations

from urllib.parse import quote, urlparse


DEEPLINK_BASE = "https://deeplink.website/link?url_ha="


def build_happ_deeplink(subscription_link: str, profile_name: str | None = None) -> str:
    if not subscription_link:
        return ""
    parsed = urlparse(subscription_link)
    if not parsed.scheme or not parsed.netloc:
        return ""
    payload = subscription_link
    if profile_name:
        payload = f"{payload}#{profile_name}"
    encoded = quote(payload, safe="")
    return f"{DEEPLINK_BASE}{encoded}"
