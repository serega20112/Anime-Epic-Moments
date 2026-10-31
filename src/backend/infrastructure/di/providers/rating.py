"""Провайдеры сценариев оценок."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.rating.get_user_ratings import GetUserRatingsUseCase
from backend.application.use_cases.rating.set_user_anime_rating import SetUserAnimeRatingUseCase
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache


class RatingUseCaseProvider(Provider):
    """Провайдер сценариев оценок."""

    @provide(scope=Scope.REQUEST)
    async def get_user_ratings(
        self,
        unit_of_work: UnitOfWorkInterface,
    ) -> GetUserRatingsUseCase:
        """Создать сценарий оценок пользователя."""
        return GetUserRatingsUseCase(unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def set_user_anime_rating(
        self,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache,
    ) -> SetUserAnimeRatingUseCase:
        """Создать сценарий выставления оценки аниме."""
        return SetUserAnimeRatingUseCase(unit_of_work, profile_overview_cache)
