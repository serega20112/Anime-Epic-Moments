"""Настройки кэша Redis и состояния безопасности."""

from __future__ import annotations

import os


def redis_enabled() -> bool:
    """Вернуть, включён ли Redis."""
    return os.getenv("REDIS_ENABLED", "1") == "1"


def redis_required() -> bool:
    """Вернуть, обязателен ли Redis для запуска приложения."""
    return os.getenv("REDIS_REQUIRED", "0") == "1"


def redis_url() -> str | None:
    """Вернуть URL подключения к Redis или None, если он выключен."""
    if not redis_enabled():
        return None
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")
