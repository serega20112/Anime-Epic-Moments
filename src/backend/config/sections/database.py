"""Database connection settings."""

from __future__ import annotations

import os


def build_default_database_url(*, async_mode: bool) -> str:
    """Build a default PostgreSQL URL from individual environment variables.

    Args:
        async_mode: Whether to return an async driver URL.

    Returns:
        str: Database URL with the appropriate driver scheme.
    """
    user = os.getenv("POSTGRES_USER", "anime_epic_moments")
    password = os.getenv("POSTGRES_PASSWORD", "anime_epic_moments")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "anime_epic_moments")
    scheme = "postgresql+asyncpg" if async_mode else "postgresql+psycopg"
    return f"{scheme}://{user}:{password}@{host}:{port}/{database}"


def normalize_database_url(value: str | None, *, async_mode: bool) -> str:
    """Normalize a database URL to the requested driver scheme.

    Args:
        value: Raw database URL from the environment.
        async_mode: Whether to return an async driver URL.

    Returns:
        str: Normalized database URL.
    """
    raw_value = str(value or "").strip()
    if not raw_value:
        return build_default_database_url(async_mode=async_mode)
    if raw_value.startswith("postgres://"):
        raw_value = f"postgresql://{raw_value[len('postgres://') :]}"
    if async_mode:
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
    if raw_value.startswith("postgresql+psycopg://"):
        return raw_value
    if raw_value.startswith("postgresql+asyncpg://"):
        return f"postgresql+psycopg://{raw_value[len('postgresql+asyncpg://') :]}"
    if raw_value.startswith("postgresql://"):
        return f"postgresql+psycopg://{raw_value[len('postgresql://') :]}"
    if raw_value.startswith("sqlite+aiosqlite:///"):
        return f"sqlite:///{raw_value[len('sqlite+aiosqlite:///') :]}"
    return raw_value


def database_url() -> str:
    """Return the async database URL.

    Returns:
        str: Normalized async database URL.
    """
    return normalize_database_url(os.getenv("DATABASE_URL"), async_mode=True)


def database_sync_url() -> str:
    """Return the sync database URL.

    Returns:
        str: Normalized sync database URL.
    """
    return normalize_database_url(os.getenv("DATABASE_URL"), async_mode=False)


def database_auto_init() -> bool:
    """Return whether the database schema should be initialized automatically.

    Returns:
        bool: True when DATABASE_AUTO_INIT is enabled.
    """
    return os.getenv("DATABASE_AUTO_INIT", "0") == "1"
