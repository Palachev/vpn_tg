from __future__ import annotations

from urllib.parse import quote, urlparse


DEEPLINK_BASE = "https://deeplink.website/link?url_ha="
PROFILE_NAME = "DagDev VPN"


def build_happ_deeplink(subscription_link: str) -> str:
    if not subscription_link:
        return ""
    parsed = urlparse(subscription_link)
    if not parsed.scheme or not parsed.netloc:
        return ""
    link_with_profile = f"{subscription_link}#{PROFILE_NAME}"
    encoded = quote(link_with_profile, safe="")
    return f"{DEEPLINK_BASE}{encoded}"
