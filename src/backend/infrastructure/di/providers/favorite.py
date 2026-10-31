"""Провайдеры сценариев избранного."""

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


class FavoriteUseCaseProvider(Provider):
    """Провайдер сценариев избранного."""

    @provide(scope=Scope.REQUEST)
    async def add_favorite(
        self,
        unit_of_work: UnitOfWorkInterface,
        recommendation_service: RecommendationService,
        profile_overview_cache: ProfileOverviewCache,
    ) -> AddFavoriteUseCase:
        """Создать сценарий добавления в избранное."""
        return AddFavoriteUseCase(unit_of_work, recommendation_service, profile_overview_cache)

    @provide(scope=Scope.REQUEST)
    async def remove_favorite(
        self,
        unit_of_work: UnitOfWorkInterface,
        recommendation_service: RecommendationService,
        profile_overview_cache: ProfileOverviewCache,
    ) -> RemoveFavoriteUseCase:
        """Создать сценарий удаления из избранного."""
        return RemoveFavoriteUseCase(unit_of_work, recommendation_service, profile_overview_cache)

    @provide(scope=Scope.REQUEST)
    async def get_favorites(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClient,
    ) -> GetFavoritesUseCase:
        """Создать сценарий списка избранного."""
        return GetFavoritesUseCase(unit_of_work, anime_api_client)

    @provide(scope=Scope.REQUEST)
    async def get_favorite_ids(
        self,
        unit_of_work: UnitOfWorkInterface,
    ) -> GetFavoriteIdsUseCase:
        """Создать сценарий списка идентификаторов избранного."""
        return GetFavoriteIdsUseCase(unit_of_work)
