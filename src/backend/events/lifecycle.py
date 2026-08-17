"""Application lifecycle (startup/shutdown) via FastAPI lifespan."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.config import Settings
from backend.infrastructure.files.database import init_db, verify_schema
from backend.utils import setup_logging

logger = logging.getLogger("anime_epic_moments")


async def _resolve_log_level(level_name: str) -> int:
    """Resolve a logging level name to its numeric value.

    Args:
        level_name: Logging level name (e.g. INFO, DEBUG).

    Returns:
        int: Numeric logging level value.
    """
    return getattr(logging, str(level_name).upper(), logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run application startup and shutdown tasks.

    Args:
        app: FastAPI application instance.

    Yields:
        None: The lifespan body.
    """
    await setup_logging(level=await _resolve_log_level(Settings.log_level))
    if Settings.database_auto_init:
        await init_db()
    else:
        await verify_schema()
    logger.info("application_started")
    yield
    logger.info("application_stopped")
