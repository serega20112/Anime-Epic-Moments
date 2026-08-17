"""LLM client that tries a primary provider and falls back to a secondary one."""

from __future__ import annotations

from typing import Any


class FailoverLLMClient:
    """Serves LLM requests from a primary provider, falling back on failure.

    Search queries and taste descriptions are requested from the primary
    provider first; when it is unconfigured, rate-limited, or returns a
    fallback mode, the request is retried against the fallback provider.
    """

    def __init__(self, primary: Any, fallback: Any):
        """Initialize the failover client.

        Args:
            primary: Primary LLM client with build_search_queries_with_meta and
                describe_taste_profile methods.
            fallback: Fallback LLM client with the same interface.
        """
        self.primary = primary
        self.fallback = fallback

    async def aclose(self) -> None:
        """Close the underlying HTTP clients of both providers."""
        for client in (self.primary, self.fallback):
            closer = getattr(client, "aclose", None)
            if closer is not None:
                await closer()

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
        """Build search queries via the primary provider, retrying the fallback.

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
        if getattr(self.primary, "api_key", None):
            queries, mode, error = await self.primary.build_search_queries_with_meta(
                description=description,
                genre_hint=genre_hint,
                year_from=year_from,
                year_to=year_to,
                min_rating=min_rating,
                age_rating=age_rating,
                allow_adult=allow_adult,
            )
            if not mode.startswith("fallback"):
                return queries, mode, error
        return await self.fallback.build_search_queries_with_meta(
            description=description,
            genre_hint=genre_hint,
            year_from=year_from,
            year_to=year_to,
            min_rating=min_rating,
            age_rating=age_rating,
            allow_adult=allow_adult,
        )

    async def describe_taste_profile(self, profile_data: dict, fallback: str) -> str:
        """Describe a taste profile via the primary provider, retrying the fallback.

        Args:
            profile_data: Dictionary of profile attributes.
            fallback: Fallback text if all providers are unavailable.

        Returns:
            str: Generated or fallback description.
        """
        primary_result = await self.primary.describe_taste_profile(profile_data, fallback)
        if primary_result != fallback:
            return primary_result
        return await self.fallback.describe_taste_profile(profile_data, fallback)
