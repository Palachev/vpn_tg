from __future__ import annotations

from urllib.parse import quote, urlparse


DEEPLINK_BASE = "https://deeplink.website/link?url_ha="


def build_happ_deeplink(subscription_link: str) -> str:
    if not subscription_link:
        return ""
    parsed = urlparse(subscription_link)
    if not parsed.scheme or not parsed.netloc:
        return ""
    encoded = quote(subscription_link, safe="")
    return f"{DEEPLINK_BASE}{encoded}"
