"""Настройки подключения к базе данных.

Проект полностью асинхронный: здесь собираются только URL с async-драйвером.
"""

from __future__ import annotations

import os


def build_default_database_url() -> str:
    """Собрать URL PostgreSQL по отдельным переменным окружения."""
    user = os.getenv("POSTGRES_USER", "anime_epic_moments")
    password = os.getenv("POSTGRES_PASSWORD", "anime_epic_moments")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "anime_epic_moments")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"


def normalize_database_url(value: str | None) -> str:
    """Привести URL базы к схеме асинхронного драйвера.

    Args:
        value: Сырой URL из окружения.

    Returns:
        str: URL с async-драйвером.
    """
    raw_value = str(value or "").strip()
    if not raw_value:
        return build_default_database_url()
    if raw_value.startswith("postgres://"):
        raw_value = f"postgresql://{raw_value[len('postgres://') :]}"
    if raw_value.startswith("postgresql+asyncpg://"):
        return raw_value
    if raw_value.startswith("postgresql+psycopg://"):
        return f"postgresql+asyncpg://{raw_value[len('postgresql+psycopg://') :]}"
    if raw_value.startswith("postgresql://"):
        return f"postgresql+asyncpg://{raw_value[len('postgresql://') :]}"
    if raw_value.startswith("sqlite+aiosqlite:///"):
        return raw_value
    if raw_value.startswith("sqlite:///"):
        return f"sqlite+aiosqlite:///{raw_value[len('sqlite:///') :]}"
    return raw_value


def database_url() -> str:
    """Вернуть URL базы данных с асинхронным драйвером."""
    return normalize_database_url(os.getenv("DATABASE_URL"))


def database_auto_init() -> bool:
    """Вернуть, инициализировать ли схему базы автоматически при старте."""
    return os.getenv("DATABASE_AUTO_INIT", "0") == "1"
