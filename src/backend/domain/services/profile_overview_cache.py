"""Abstract profile overview cache interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ProfileOverviewCacheInterface(ABC):
    """Interface for caching user profile overviews."""

    @abstractmethod
    async def get_overview(self, user_id: int) -> Any:
        """Get cached profile overview.

        Args:
            user_id: The user identifier.

        Returns:
            Any: Cached ProfileOverview or None.
        """

    @abstractmethod
    async def set_overview(self, user_id: int, overview: Any) -> Any:
        """Store profile overview in cache.

        Args:
            user_id: The user identifier.
            overview: ProfileOverview to cache.

        Returns:
            Any: The stored overview.
        """

    @abstractmethod
    async def get_ai_summary(self, user_id: int) -> str | None:
        """Get cached AI taste summary.

        Args:
            user_id: The user identifier.

        Returns:
            str | None: Cached summary or None.
        """

    @abstractmethod
    async def set_ai_summary(self, user_id: int, summary: str) -> None:
        """Store AI taste summary in cache.

        Args:
            user_id: The user identifier.
            summary: Summary text to cache.
        """

    @abstractmethod
    async def invalidate(self, user_id: int) -> None:
        """Invalidate cached data for a user.

        Args:
            user_id: The user identifier.
        """
