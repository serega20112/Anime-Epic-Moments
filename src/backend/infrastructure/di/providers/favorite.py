"""Favorite use case providers."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.services.recommendation_service import RecommendationService
from backend.application.use_cases import GetFavoritesUseCase
from backend.application.use_cases.favorite.add_favorite import AddFavoriteUseCase
from backend.application.use_cases.favorite.get_favorite_ids import GetFavoriteIdsUseCase
from backend.application.use_cases.favorite.remove_favorite import RemoveFavoriteUseCase
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from backend.infrastructure.external import AnimeApiClient
from backend.infrastructure.repositories.favorite_repository import FavoriteRepository


class FavoriteUseCaseProvider(Provider):
    """Provide favorite use cases."""

    @provide(scope=Scope.REQUEST)
    async def add_favorite(
        self,
        favorite_repository: FavoriteRepository,
        unit_of_work: UnitOfWorkInterface,
        recommendation_service: RecommendationService,
        profile_overview_cache: ProfileOverviewCache,
    ) -> AddFavoriteUseCase:
        """Provide the add favorite use case.

        Args:
            favorite_repository: Favorite repository.
            unit_of_work: Transaction boundary.
            recommendation_service: Recommendation service.
            profile_overview_cache: Profile overview cache.

        Returns:
            AddFavoriteUseCase: Configured use case.
        """
        return AddFavoriteUseCase(
            favorite_repository,
            unit_of_work,
            recommendation_service,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def remove_favorite(
        self,
        favorite_repository: FavoriteRepository,
        unit_of_work: UnitOfWorkInterface,
        recommendation_service: RecommendationService,
        profile_overview_cache: ProfileOverviewCache,
    ) -> RemoveFavoriteUseCase:
        """Provide the remove favorite use case.

        Args:
            favorite_repository: Favorite repository.
            unit_of_work: Transaction boundary.
            recommendation_service: Recommendation service.
            profile_overview_cache: Profile overview cache.

        Returns:
            RemoveFavoriteUseCase: Configured use case.
        """
        return RemoveFavoriteUseCase(
            favorite_repository,
            unit_of_work,
            recommendation_service,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def get_favorites(
        self,
        favorite_repository: FavoriteRepository,
        anime_api_client: AnimeApiClient,
    ) -> GetFavoritesUseCase:
        """Provide the get favorites use case.

        Args:
            favorite_repository: Favorite repository.
            anime_api_client: Anime API client.

        Returns:
            GetFavoritesUseCase: Configured use case.
        """
        return GetFavoritesUseCase(favorite_repository, anime_api_client)

    @provide(scope=Scope.REQUEST)
    async def get_favorite_ids(
        self,
        favorite_repository: FavoriteRepository,
    ) -> GetFavoriteIdsUseCase:
        """Provide the get favorite ids use case.

        Args:
            favorite_repository: Favorite repository.

        Returns:
            GetFavoriteIdsUseCase: Configured use case.
        """
        return GetFavoriteIdsUseCase(favorite_repository)
