"""Abstract LLM client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMClientInterface(ABC):
    """Interface for LLM-based AI clients."""

    @abstractmethod
    async def build_search_queries_with_meta(
        self,
        description: str,
        genre_hint: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        min_rating: int | None = None,
        age_rating: str = "all",
        allow_adult: bool = False,
    ) -> tuple[list[str], str, str | None]:
        """Build multiple search queries plus provider mode metadata.

        Args:
            description: Natural language anime description.
            genre_hint: Optional genre hint.
            year_from: Optional start year filter.
            year_to: Optional end year filter.
            min_rating: Optional minimum rating.
            age_rating: Age rating constraint.
            allow_adult: Whether adult content is allowed.

        Returns:
            tuple[list[str], str, str | None]: Queries, mode, and optional error.
        """

    @abstractmethod
    async def describe_taste_profile(self, profile_data: dict, fallback: str) -> str:
        """Generate a taste profile description.

        Args:
            profile_data: Dictionary of profile attributes.
            fallback: Fallback text if AI is unavailable.

        Returns:
            str: Generated or fallback description.
        """

    @abstractmethod
    async def search_by_description(self, description: str, limit: int = 5) -> list[Any]:
        """Search anime by natural language description.

        Args:
            description: Natural language anime description.
            limit: Maximum number of results.

        Returns:
            list[Any]: List of anime data objects.
        """
