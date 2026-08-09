"""Use case for generating anime recommendations."""

from __future__ import annotations

from backend.domain import RecommendationResult
from backend.domain.services import (
    RecommendationServiceInterface as RecommendationService,
)


class GenerateRecommendationsUseCase:
    """Generate personalized anime recommendations for a user."""

    def __init__(self, service: RecommendationService):
        """Initialize the use case.

        Args:
            service: Recommendation service.
        """
        self.service = service

    async def execute(self, user_id: int, limit: int = 5) -> list[RecommendationResult]:
        """Return recommendations for the given user.

        Args:
            user_id: User identifier.
            limit: Maximum number of recommendations.

        Returns:
            list[RecommendationResult]: Recommended anime list.
        """
        return await self.service.generate(user_id, limit)
