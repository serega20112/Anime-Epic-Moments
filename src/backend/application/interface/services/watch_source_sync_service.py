"""Abstract watch source sync service interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class WatchSourceSyncServiceInterface(ABC):
    """Interface for syncing watch sources."""

    @abstractmethod
    async def sync_sources(self, anime_id: int) -> list[Any]:
        """Sync watch sources for an anime.

        Args:
            anime_id: The anime identifier.

        Returns:
            list[Any]: List of watch source objects.
        """

    @abstractmethod
    async def add_watch_source(self, source_data: dict[str, Any]) -> Any:
        """Add a watch source.

        Args:
            source_data: Dictionary with source information.

        Returns:
            Any: The created watch source.
        """
