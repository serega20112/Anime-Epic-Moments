"""Media proxy URL policy: allowlist, HLS detection, user-agent."""

from __future__ import annotations

from urllib.parse import urlparse

ALLOWED_MEDIA_HOST_SUFFIXES: tuple[str, ...] = (
    "libria.fun",
    "anilibria.top",
    "anilibria.tv",
    "kodikplayer.com",
    "kodik.info",
    "kodik.biz",
    "kodikapi.com",
)

_DEFAULT_USER_AGENT = "Mozilla/5.0"


def is_allowed_media_url(value: str) -> bool:
    """Check whether a URL host is on the media allowlist.

    Args:
        value: Raw URL string.

    Returns:
        bool: True when the URL is allowed.
    """
    parsed = urlparse(str(value or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    hostname = (parsed.hostname or "").lower()
    return any(
        hostname == suffix or hostname.endswith(f".{suffix}")
        for suffix in ALLOWED_MEDIA_HOST_SUFFIXES
    )


def is_hls_manifest(upstream_url: str, content_type: str) -> bool:
    """Detect whether the upstream response is an HLS manifest.

    Args:
        upstream_url: Upstream URL.
        content_type: Upstream content type.

    Returns:
        bool: True for HLS manifests.
    """
    return ".m3u8" in upstream_url.lower() or "mpegurl" in content_type


def browser_user_agent(user_agent: str | None) -> str:
    """Return a browser-like User-Agent, falling back to a default.

    Args:
        user_agent: Client-provided User-Agent or None.

    Returns:
        str: User-Agent string.
    """
    normalized = str(user_agent or "").strip()
    return normalized or _DEFAULT_USER_AGENT