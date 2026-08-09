"""Abstract recommendation service interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class RecommendationServiceInterface(ABC):
    """Interface for generating anime recommendations."""

    @abstractmethod
    async def generate_recommendations(self, user_id: int) -> list[Any]:
        """Generate recommendations for a user.

        Args:
            user_id: The user identifier.

        Returns:
            list[Any]: List of recommendation objects.
        """

    @abstractmethod
    async def refresh_recommendations(self, user_id: int) -> list[Any]:
        """Refresh recommendations for a user.

        Args:
            user_id: The user identifier.

        Returns:
            list[Any]: List of refreshed recommendation objects.
        """
