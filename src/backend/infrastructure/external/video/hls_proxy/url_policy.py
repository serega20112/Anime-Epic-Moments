"""Политика адресов медиапрокси: список хостов, определение HLS, User-Agent."""

from __future__ import annotations

from urllib.parse import urlparse

ALLOWED_MEDIA_HOST_SUFFIXES: tuple[str, ...] = (
    "libria.fun",
    "anilibria.top",
    "anilibria.tv",
    "anilibria.host",
    "sameband.studio",
    "aniboom.one",
    "hanime.tv",
    "hanime.com",
    "mushy.tv",
    "sibnet.ru",
    "kinobox.tv",
    "kodikplayer.com",
    "kodik.info",
    "kodik.biz",
    "kodikapi.com",
    "youtube.com",
    "youtube-nocookie.com",
    "ytimg.com",
    "googlevideo.com",
    "ok.ru",
    "vk.com",
    "vkvideo.ru",
    "mail.ru",
    "hentaigasm.com",
    "hgasm1.com",
    "hgasm2.com",
    "hgasm3.com",
)

_DEFAULT_USER_AGENT = "Mozilla/5.0"


async def is_allowed_media_url(value: str) -> bool:
    """Проверить, разрешён ли хост адреса для медиапрокси."""
    parsed = urlparse(str(value or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    hostname = (parsed.hostname or "").lower()
    return any(
        hostname == suffix or hostname.endswith(f".{suffix}")
        for suffix in ALLOWED_MEDIA_HOST_SUFFIXES
    )


async def is_hls_manifest(upstream_url: str, content_type: str) -> bool:
    """Определить, является ли ответ источника HLS-манифестом."""
    return ".m3u8" in upstream_url.lower() or "mpegurl" in content_type


async def browser_user_agent(user_agent: str | None) -> str:
    """Вернуть браузерный User-Agent или значение по умолчанию."""
    normalized = str(user_agent or "").strip()
    return normalized or _DEFAULT_USER_AGENT
