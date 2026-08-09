"""Application lifecycle event handlers (startup/shutdown)."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from backend.infrastructure.files.database import init_db

from backend.config import Settings
from backend.utils import setup_logging

logger = logging.getLogger("anime_epic_moments")


def _resolve_log_level(level_name: str) -> int:
    """Resolve a logging level name to its numeric value.

    Args:
        level_name: Logging level name (e.g. INFO, DEBUG).

    Returns:
        int: Numeric logging level value.
    """
    return getattr(logging, str(level_name).upper(), logging.INFO)


def register_lifecycle_handlers(app: FastAPI) -> None:
    """Register startup and shutdown handlers on the FastAPI app.

    Args:
        app: FastAPI application instance.
    """

    @app.on_event("startup")
    async def startup() -> None:
        """Initialize logging and database when the app starts."""
        setup_logging(level=_resolve_log_level(Settings.log_level))
        if Settings.database_auto_init:
            await init_db()
        logger.info("application_started")

    @app.on_event("shutdown")
    async def shutdown() -> None:
        """Clean up resources when the app shuts down."""
        logger.info("application_stopped")
