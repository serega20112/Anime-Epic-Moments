"""Настройки каталога аниме: Shikimori как источник тайтлов и id."""

from __future__ import annotations

import os

from backend.config.sections.external._common import _clean_secret


def shikimori_enabled() -> bool:
    """Вернуть, включено ли обогащение русскими названиями через Shikimori."""
    return os.getenv("SHIKIMORI_ENABLED", "1") == "1"


def shikimori_api_url() -> str:
    """Вернуть базовый адрес API Shikimori."""
    return os.getenv("SHIKIMORI_API_URL", "https://shikimori.one/api")


def shikimori_token() -> str | None:
    """Вернуть необязательный токен Shikimori.

    Публичные методы чтения работают и без токена; с токеном поднимается лимит
    запросов на IP.

    Returns:
        str | None: Токен Shikimori или None.
    """
    return _clean_secret(os.getenv("SHIKIMORI_TOKEN"))


def shikimori_user_agent() -> str:
    """Вернуть User-Agent для запросов к API Shikimori.

    Shikimori требует опознаваемый User-Agent в каждом запросе.

    Returns:
        str: Строка User-Agent.
    """
    return os.getenv(
        "SHIKIMORI_USER_AGENT",
        "AnimeEpicMoments/1.0 (anime-epic-moments)",
    )
