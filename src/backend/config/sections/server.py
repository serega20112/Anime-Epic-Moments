"""Настройки HTTP-сервера и веб-приложения."""

from __future__ import annotations

import os


def app_host() -> str:
    """Вернуть адрес привязки веб-сервера."""
    return os.getenv("APP_HOST", "0.0.0.0")


def app_port() -> int:
    """Вернуть порт привязки веб-сервера."""
    return int(os.getenv("APP_PORT", "5000"))


def app_debug() -> bool:
    """Вернуть, включён ли режим отладки."""
    return os.getenv("APP_DEBUG", "0") == "1"


def log_level() -> str:
    """Вернуть уровень логирования приложения."""
    return os.getenv("LOG_LEVEL", "INFO")


def log_format() -> str:
    """Вернуть формат вывода журнала: json либо text."""
    return os.getenv("LOG_FORMAT", "json")


def max_request_bytes() -> int:
    """Вернуть предельный размер тела запроса в байтах."""
    return int(os.getenv("MAX_REQUEST_BYTES", "1048576"))


def app_base_url() -> str:
    """Вернуть публичный базовый адрес приложения."""
    return os.getenv("APP_BASE_URL", "http://127.0.0.1:5000")


def app_allowed_origins() -> list[str]:
    """Вернуть разрешённые источники для кросс-доменных запросов."""
    return [
        item.strip() for item in os.getenv("APP_ALLOWED_ORIGINS", "").split(",") if item.strip()
    ]
