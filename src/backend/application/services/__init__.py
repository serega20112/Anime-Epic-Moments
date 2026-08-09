"""Facade re-exports for backend.application.services."""

from __future__ import annotations

from backend.application.services.watch_source_sync_service import WatchSourceSyncService

__all__ = [
    "WatchSourceSyncService",
]
