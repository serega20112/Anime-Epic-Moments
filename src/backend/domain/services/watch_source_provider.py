"""Abstract watch source provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class WatchSourceProviderInterface(ABC):
    """Interface for fetching watch sources from external providers."""

    @abstractmethod
    async def get_sources(self, anime_id: int) -> list[Any]:
        """Get watch sources for an anime.

        Args:
            anime_id: The anime identifier.

        Returns:
            list[Any]: List of watch source objects.
        """

    @abstractmethod
    async def close(self) -> None:
        """Close provider resources and connections."""
