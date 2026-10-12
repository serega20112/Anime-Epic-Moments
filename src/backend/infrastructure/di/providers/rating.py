"""Rating use case providers."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.rating.get_user_ratings import GetUserRatingsUseCase
from backend.application.use_cases.rating.set_user_anime_rating import SetUserAnimeRatingUseCase
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from backend.infrastructure.repositories.rating_repository import RatingRepository


class RatingUseCaseProvider(Provider):
    """Provide rating use cases."""

    @provide(scope=Scope.REQUEST)
    async def get_user_ratings(
        self,
        rating_repository: RatingRepository,
    ) -> GetUserRatingsUseCase:
        """Provide the get user ratings use case.

        Args:
            rating_repository: Rating repository.

        Returns:
            GetUserRatingsUseCase: Configured use case.
        """
        return GetUserRatingsUseCase(rating_repository)

    @provide(scope=Scope.REQUEST)
    async def set_user_anime_rating(
        self,
        rating_repository: RatingRepository,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache,
    ) -> SetUserAnimeRatingUseCase:
        """Provide the set user anime rating use case.

        Args:
            rating_repository: Rating repository.
            unit_of_work: Transaction boundary.
            profile_overview_cache: Profile overview cache.

        Returns:
            SetUserAnimeRatingUseCase: Configured use case.
        """
        return SetUserAnimeRatingUseCase(
            rating_repository,
            unit_of_work,
            profile_overview_cache,
        )
