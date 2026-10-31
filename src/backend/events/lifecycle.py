"""Жизненный цикл приложения: запуск и остановка через lifespan FastAPI."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.config import Settings
from backend.infrastructure.database.session import init_db, verify_schema
from backend.utils import setup_logging

logger = logging.getLogger("anime_epic_moments")


def _resolve_log_level(level_name: str) -> int:
    """Преобразовать имя уровня логирования в числовое значение.

    Args:
        level_name: Имя уровня из конфигурации.

    Returns:
        int: Числовой уровень; при неизвестном имени возвращается INFO.
    """
    return getattr(logging, str(level_name).upper(), logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Выполнить задачи запуска и остановки приложения."""
    setup_logging(level=_resolve_log_level(Settings.log_level), fmt=Settings.log_format)
    if Settings.database_auto_init:
        await init_db()
    else:
        await verify_schema()
    logger.info("application_started")
    yield
    logger.info("application_stopped")
