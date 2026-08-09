"""Abstract LLM client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMClientInterface(ABC):
    """Interface for LLM-based AI clients."""

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
