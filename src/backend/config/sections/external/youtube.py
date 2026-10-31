"""Настройки YouTube: ключ API, адрес и разрешённые каналы."""

from __future__ import annotations

import os

from backend.config.sections.external._common import _clean_secret


def youtube_api_key() -> str | None:
    """Вернуть ключ YouTube Data API."""
    return _clean_secret(os.getenv("YOUTUBE_API_KEY"))


def youtube_api_url() -> str:
    """Вернуть базовый адрес YouTube Data API."""
    return os.getenv("YOUTUBE_API_URL", "https://www.googleapis.com/youtube/v3")


def youtube_allowed_channel_ids() -> list[str]:
    """Вернуть список разрешённых каналов YouTube."""
    return [
        item.strip()
        for item in os.getenv("YOUTUBE_ALLOWED_CHANNEL_IDS", "").split(",")
        if item.strip()
    ]
