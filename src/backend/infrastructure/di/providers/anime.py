"""Anime, recommendations, and profile overview use case providers."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.services import WatchSourceSyncService
from backend.application.services.recommendation_service import RecommendationService
from backend.application.use_cases import (
    AskAiRecommendationsUseCase,
    FilterAnimeCatalogUseCase,
    GenerateRecommendationsUseCase,
    GetProfileOverviewUseCase,
    GetSeasonPopularUseCase,
    RefreshRecommendationsUseCase,
    SearchAnimeUseCase,
)
from backend.application.use_cases.anime.autocomplete_anime import AutocompleteAnimeUseCase
from backend.application.use_cases.anime.get_home_page import GetHomePageUseCase
from backend.application.use_cases.anime.search_anime_by_description import (
    SearchAnimeByDescriptionUseCase,
)
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from backend.infrastructure.external import AnimeApiClient
from backend.infrastructure.external.failover_llm_client import FailoverLLMClient
from backend.infrastructure.repositories.favorite_repository import FavoriteRepository
from backend.infrastructure.repositories.highlight_repository import HighlightRepository
from backend.infrastructure.repositories.user_repository import UserRepository
from backend.infrastructure.repositories.watch_repository import WatchRepository


class AnimeUseCaseProvider(Provider):
    """Provide anime, recommendation, and profile overview use cases."""

    @provide(scope=Scope.REQUEST)
    async def get_profile_overview(
        self,
        user_repository: UserRepository,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        favorite_repository: FavoriteRepository,
        watch_repository: WatchRepository,
        llm_client: FailoverLLMClient,
        profile_overview_cache: ProfileOverviewCache,
    ) -> GetProfileOverviewUseCase:
        """Provide the get profile overview use case.

        Args:
            user_repository: User repository.
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            favorite_repository: Favorite repository.
            watch_repository: Watch repository.
            llm_client: LLM client.
            profile_overview_cache: Profile overview cache.

        Returns:
            GetProfileOverviewUseCase: Configured use case.
        """
        return GetProfileOverviewUseCase(
            user_repository,
            highlight_repository,
            anime_api_client,
            favorite_repository,
            watch_repository,
            llm_client,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    async def search_anime(self, anime_api_client: AnimeApiClient) -> SearchAnimeUseCase:
        """Provide the search anime use case.

        Args:
            anime_api_client: Anime API client.

        Returns:
            SearchAnimeUseCase: Configured use case.
        """
        return SearchAnimeUseCase(anime_api_client)

    @provide(scope=Scope.REQUEST)
    async def search_anime_by_description(
        self,
        anime_api_client: AnimeApiClient,
        llm_client: FailoverLLMClient,
    ) -> SearchAnimeByDescriptionUseCase:
        """Provide the search by description use case.

        Args:
            anime_api_client: Anime API client.
            llm_client: LLM client.

        Returns:
            SearchAnimeByDescriptionUseCase: Configured use case.
        """
        return SearchAnimeByDescriptionUseCase(anime_api_client, llm_client)

    @provide(scope=Scope.REQUEST)
    async def autocomplete_anime(
        self,
        anime_api_client: AnimeApiClient,
    ) -> AutocompleteAnimeUseCase:
        """Provide the autocomplete use case.

        Args:
            anime_api_client: Anime API client.

        Returns:
            AutocompleteAnimeUseCase: Configured use case.
        """
        return AutocompleteAnimeUseCase(anime_api_client)

    @provide(scope=Scope.REQUEST)
    async def get_home_page(self) -> GetHomePageUseCase:
        """Provide the home page use case.

        Returns:
            GetHomePageUseCase: Configured use case.
        """
        return GetHomePageUseCase()

    @provide(scope=Scope.REQUEST)
    async def filter_anime_catalog(
        self,
        anime_api_client: AnimeApiClient,
        watch_repository: WatchRepository,
        watch_source_sync_service: WatchSourceSyncService,
    ) -> FilterAnimeCatalogUseCase:
        """Provide the anime catalog filter use case.

        Args:
            anime_api_client: Anime API client.
            watch_repository: Watch repository for local translation lookup.
            watch_source_sync_service: Watch source sync service for
                availability checks.

        Returns:
            FilterAnimeCatalogUseCase: Configured use case.
        """
        return FilterAnimeCatalogUseCase(
            anime_api_client,
            watch_repository,
            watch_source_sync_service,
        )

    @provide(scope=Scope.REQUEST)
    async def get_season_popular(
        self,
        anime_api_client: AnimeApiClient,
    ) -> GetSeasonPopularUseCase:
        """Provide the season popular use case.

        Args:
            anime_api_client: Anime API client.

        Returns:
            GetSeasonPopularUseCase: Configured use case.
        """
        return GetSeasonPopularUseCase(anime_api_client)

    @provide(scope=Scope.REQUEST)
    async def generate_recommendations(
        self,
        recommendation_service: RecommendationService,
    ) -> GenerateRecommendationsUseCase:
        """Provide the generate recommendations use case.

        Args:
            recommendation_service: Recommendation service.

        Returns:
            GenerateRecommendationsUseCase: Configured use case.
        """
        return GenerateRecommendationsUseCase(recommendation_service)

    @provide(scope=Scope.REQUEST)
    async def ask_ai_recommendations(
        self,
        favorite_repository: FavoriteRepository,
        anime_api_client: AnimeApiClient,
        llm_client: FailoverLLMClient,
    ) -> AskAiRecommendationsUseCase:
        """Provide the ask AI recommendations use case.

        Args:
            favorite_repository: Favorite repository.
            anime_api_client: Anime API client.
            llm_client: LLM client.

        Returns:
            AskAiRecommendationsUseCase: Configured use case.
        """
        return AskAiRecommendationsUseCase(
            favorite_repository,
            anime_api_client,
            llm_client,
        )

    @provide(scope=Scope.REQUEST)
    async def refresh_recommendations(
        self,
        recommendation_service: RecommendationService,
    ) -> RefreshRecommendationsUseCase:
        """Provide the refresh recommendations use case.

        Args:
            recommendation_service: Recommendation service.

        Returns:
            RefreshRecommendationsUseCase: Configured use case.
        """
        return RefreshRecommendationsUseCase(recommendation_service)
