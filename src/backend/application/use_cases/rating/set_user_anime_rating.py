from __future__ import annotations

from backend.application.interface.repositories.rating_repository import RatingRepository
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain import UserAnimeRating


class SetUserAnimeRatingUseCase:
    """Выставляет или обновляет оценку пользователя по аниме."""

    def __init__(
        self,
        rating_repo: RatingRepository,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        """Initialize the use case.

        Args:
            rating_repo: Rating repository port.
            unit_of_work: Transaction boundary.
            profile_overview_cache: Optional profile cache.
        """
        self.rating_repo = rating_repo
        self.unit_of_work = unit_of_work
        self.profile_overview_cache = profile_overview_cache

    async def execute(self, user_id: int, anime_id: int, score: int) -> UserAnimeRating:
        """Persist a rating within a transaction."""
        async with self.unit_of_work:
            return await self._execute(user_id, anime_id, score)

    async def _execute(self, user_id: int, anime_id: int, score: int) -> UserAnimeRating:
        rating = UserAnimeRating(user_id=user_id, anime_id=anime_id, score=score)
        result = await self.rating_repo.upsert(rating)
        if self.profile_overview_cache is not None:
            await self.profile_overview_cache.invalidate_overview(int(user_id))
        return result
