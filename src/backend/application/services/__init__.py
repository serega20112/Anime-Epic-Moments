"""Сервисы application, не зависящие от HTTP и базы."""

from __future__ import annotations

from backend.application.services.watch_source_service import WatchSourceSyncService

__all__ = [
    "WatchSourceSyncService",
]
