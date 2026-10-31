"""Провайдеры сценариев каталога, рекомендаций и обзора профиля."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.services import WatchSourceSyncService
from backend.application.services.recommendation_service import RecommendationService
from backend.application.use_cases import (
    AskAiRecommendationsUseCase,
    FilterAnimeCatalogUseCase,
    GenerateRecommendationsUseCase,
    GetLikedHighlightsUseCase,
    GetProfileOverviewUseCase,
    GetSavedHighlightsUseCase,
    GetSeasonPopularUseCase,
    GetUserHighlightsUseCase,
    RefreshRecommendationsUseCase,
    SearchAnimeUseCase,
)
from backend.application.use_cases.anime.autocomplete_anime import AutocompleteAnimeUseCase
from backend.application.use_cases.anime.get_home_page import GetHomePageUseCase
from backend.application.use_cases.anime.search_anime_by_description import (
    SearchAnimeByDescriptionUseCase,
)
from backend.domain.policies.anime_safety_policy import AnimeSafetyPolicy
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from backend.infrastructure.external import AnimeApiClient
from backend.infrastructure.external.llm import FailoverLLMClient


class AnimeUseCaseProvider(Provider):
    """Провайдер сценариев каталога, рекомендаций и обзора профиля."""

    @provide(scope=Scope.REQUEST)
    async def get_profile_overview(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClient,
        llm_client: FailoverLLMClient,
        profile_overview_cache: ProfileOverviewCache,
        get_user_highlights: GetUserHighlightsUseCase,
        get_liked_highlights: GetLikedHighlightsUseCase,
        get_saved_highlights: GetSavedHighlightsUseCase,
    ) -> GetProfileOverviewUseCase:
        """Создать сценарий обзора профиля."""
        return GetProfileOverviewUseCase(
            unit_of_work,
            anime_api_client,
            llm_client,
            profile_overview_cache,
            get_user_highlights,
            get_liked_highlights,
            get_saved_highlights,
        )

    @provide(scope=Scope.REQUEST)
    async def search_anime(
        self,
        anime_api_client: AnimeApiClient,
    ) -> SearchAnimeUseCase:
        """Создать сценарий поиска аниме."""
        return SearchAnimeUseCase(anime_api_client)

    @provide(scope=Scope.REQUEST)
    async def search_anime_by_description(
        self,
        anime_api_client: AnimeApiClient,
        llm_client: FailoverLLMClient,
        safety_policy: AnimeSafetyPolicy,
    ) -> SearchAnimeByDescriptionUseCase:
        """Создать сценарий поиска по описанию."""
        return SearchAnimeByDescriptionUseCase(anime_api_client, llm_client, safety_policy)

    @provide(scope=Scope.REQUEST)
    async def autocomplete_anime(
        self,
        anime_api_client: AnimeApiClient,
    ) -> AutocompleteAnimeUseCase:
        """Создать сценарий автодополнения."""
        return AutocompleteAnimeUseCase(anime_api_client)

    @provide(scope=Scope.REQUEST)
    async def get_home_page(self) -> GetHomePageUseCase:
        """Создать сценарий главной страницы."""
        return GetHomePageUseCase()

    @provide(scope=Scope.REQUEST)
    async def filter_anime_catalog(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClient,
        watch_source_sync_service: WatchSourceSyncService,
    ) -> FilterAnimeCatalogUseCase:
        """Создать сценарий фильтрации каталога."""
        return FilterAnimeCatalogUseCase(
            unit_of_work,
            anime_api_client,
            watch_source_sync_service,
        )

    @provide(scope=Scope.REQUEST)
    async def get_season_popular(
        self,
        anime_api_client: AnimeApiClient,
    ) -> GetSeasonPopularUseCase:
        """Создать сценарий популярного за сезон."""
        return GetSeasonPopularUseCase(anime_api_client)

    @provide(scope=Scope.REQUEST)
    async def generate_recommendations(
        self,
        unit_of_work: UnitOfWorkInterface,
        recommendation_service: RecommendationService,
    ) -> GenerateRecommendationsUseCase:
        """Создать сценарий подбора рекомендаций."""
        return GenerateRecommendationsUseCase(unit_of_work, recommendation_service)

    @provide(scope=Scope.REQUEST)
    async def ask_ai_recommendations(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClient,
        llm_client: FailoverLLMClient,
    ) -> AskAiRecommendationsUseCase:
        """Создать сценарий запроса рекомендаций у ИИ."""
        return AskAiRecommendationsUseCase(
            unit_of_work,
            anime_api_client,
            llm_client,
        )

    @provide(scope=Scope.REQUEST)
    async def refresh_recommendations(
        self,
        unit_of_work: UnitOfWorkInterface,
        recommendation_service: RecommendationService,
    ) -> RefreshRecommendationsUseCase:
        """Создать сценарий обновления рекомендаций."""
        return RefreshRecommendationsUseCase(unit_of_work, recommendation_service)
