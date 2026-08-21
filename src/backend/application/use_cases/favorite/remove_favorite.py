"""Use case for removing an anime from favorites."""

from __future__ import annotations

from backend.application.interface.repositories.favorite_repository import FavoriteRepository
from backend.application.interface.services import (
    RecommendationServiceInterface as RecommendationService,
)
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface


class RemoveFavoriteUseCase:
    """Remove an anime from the user's favorites."""

    def __init__(
        self,
        repo: FavoriteRepository,
        unit_of_work: UnitOfWorkInterface,
        recommendation_service: RecommendationService | None = None,
        profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        """Initialize the use case.

        Args:
            repo: Favorite repository.
            recommendation_service: Optional recommendation cache invalidator.
            profile_overview_cache: Optional profile overview cache invalidator.
            unit_of_work: Transaction boundary.
        """
        self.repo = repo
        self.recommendation_service = recommendation_service
        self.profile_overview_cache = profile_overview_cache
        self.unit_of_work = unit_of_work

    async def execute(self, user_id: int, anime_id: int):
        """Remove a favorite within a transaction."""
        async with self.unit_of_work:
            await self._execute(user_id, anime_id)

    async def _execute(self, user_id: int, anime_id: int):
        """Remove a favorite and invalidate dependent caches.

        Args:
            user_id: User identifier.
            anime_id: Anime identifier.
        """
        await self.repo.remove(user_id, anime_id)
        if self.recommendation_service:
            await self.recommendation_service.invalidate_user(int(user_id))
        if self.profile_overview_cache is not None:
            await self.profile_overview_cache.invalidate_user(
                int(user_id),
                include_ai_summary=True,
            )
