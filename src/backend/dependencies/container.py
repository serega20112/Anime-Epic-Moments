"""
DI контейнер приложения
"""

from functools import cached_property

from src.backend.infrastructure.files.database import get_session
from src.backend.infrastructure.cache.recommendation_cache import RecommendationCache
from src.backend.infrastructure.cache.highlight_dashboard_cache import (
    HighlightDashboardCache,
)
from src.backend.infrastructure.cache.key_value_store import KeyValueStore
from src.backend.infrastructure.repositories.user_repository import UserRepository
from src.backend.infrastructure.repositories.highlight_repository import (
    HighlightRepository,
)
from src.backend.infrastructure.repositories.favorite_repository import (
    FavoriteRepository,
)
from src.backend.infrastructure.repositories.watch_repository import WatchRepository
from src.backend.use_case.auth.register_user import RegisterUserUseCase
from src.backend.use_case.auth.login_user import LoginUserUseCase
from src.backend.use_case.auth.logout_user import LogoutUserUseCase
from src.backend.use_case.auth.update_user_profile import UpdateUserProfileUseCase
from src.backend.use_case.auth.request_password_reset import RequestPasswordResetUseCase
from src.backend.use_case.auth.reset_password import ResetPasswordUseCase
from src.backend.use_case.highlight.create_highlight import CreateHighlightUseCase
from src.backend.use_case.highlight.delete_highlight import DeleteHighlightUseCase
from src.backend.use_case.highlight.edit_highlight import EditHighlightUseCase
from src.backend.use_case.highlight.get_user_highlights import GetUserHighlightsUseCase
from src.backend.use_case.highlight.get_public_top_highlights import (
    GetPublicTopHighlightsUseCase,
)
from src.backend.use_case.favorite.add_favorite import AddFavoriteUseCase
from src.backend.use_case.favorite.remove_favorite import RemoveFavoriteUseCase
from src.backend.use_case.favorite.get_favorites import GetFavoritesUseCase
from src.backend.use_case.anime.search_anime import SearchAnimeUseCase
from src.backend.use_case.anime.search_anime_by_description import (
    SearchAnimeByDescriptionUseCase,
)
from src.backend.use_case.anime.autocomplete_anime import AutocompleteAnimeUseCase
from src.backend.use_case.anime.get_season_popular import GetSeasonPopularUseCase
from src.backend.use_case.recommendation.generate_recommendations import (
    GenerateRecommendationsUseCase,
)
from src.backend.use_case.recommendation.refresh_recommendations import (
    RefreshRecommendationsUseCase,
)
from src.backend.use_case.watch.create_watch_highlight import (
    CreateWatchHighlightUseCase,
)
from src.backend.use_case.watch.get_watch_page import GetWatchPageUseCase
from src.backend.use_case.watch.save_viewing_session import SaveViewingSessionUseCase
from src.backend.use_case.watch.sync_watch_sources import SyncWatchSourcesUseCase
from src.backend.use_case.watch.upsert_user_anime_status import (
    UpsertUserAnimeStatusUseCase,
)
from src.backend.services.recommendation_service import RecommendationService
from src.backend.services.watch_source_sync_service import WatchSourceSyncService
from src.backend.infrastructure.external.anilibria_client import AniLibriaClient
from src.backend.infrastructure.external.anime_api_client import AnimeApiClient
from src.backend.infrastructure.external.huggingface_llm_client import (
    HuggingFaceLLMClient,
)
from src.backend.infrastructure.external.justwatch_client import JustWatchClient
from src.backend.infrastructure.external.kodik_client import KodikClient
from src.backend.infrastructure.external.password_reset_mailer import (
    PasswordResetMailer,
)
from src.backend.infrastructure.external.youtube_client import YouTubeClient
from src.backend.infrastructure.security.password_service import PasswordService
from src.backend.infrastructure.security.jwt_service import JWTService
from src.backend.infrastructure.security.rate_limiter import RateLimiter
from src.backend.infrastructure.security.token_blocklist import TokenBlocklist
from src.backend.dependencies.settings import Settings


class Container:
    """
    Dependency Injection контейнер
    """

    @cached_property
    def db_session(self):
        return get_session()

    @cached_property
    def key_value_store(self):
        return KeyValueStore(
            redis_url=Settings.redis_url,
            namespace="anime_epic_moments",
            required=Settings.redis_required,
        )

    @cached_property
    def anime_api_client(self):
        return AnimeApiClient(store=self.key_value_store)

    @cached_property
    def kodik_client(self):
        return KodikClient()

    @cached_property
    def anilibria_client(self):
        return AniLibriaClient()

    @cached_property
    def youtube_client(self):
        return YouTubeClient()

    @cached_property
    def justwatch_client(self):
        return JustWatchClient()

    @cached_property
    def hf_llm_client(self):
        if not Settings.hf_token:
            print(
                "! HF_TOKEN не задан: поиск по описанию работает в fallback-режиме без LLM"
            )
        return HuggingFaceLLMClient(
            api_key=Settings.hf_token,
            model=Settings.hf_model,
            provider=Settings.hf_provider,
            api_url=Settings.hf_api_url,
        )

    @cached_property
    def user_repository(self):
        return UserRepository(self.db_session)

    @cached_property
    def highlight_repository(self):
        return HighlightRepository(self.db_session)

    @cached_property
    def favorite_repository(self):
        return FavoriteRepository(self.db_session)

    @cached_property
    def watch_repository(self):
        return WatchRepository(self.db_session)

    @cached_property
    def recommendation_cache(self):
        return RecommendationCache(store=self.key_value_store)

    @cached_property
    def highlight_dashboard_cache(self):
        return HighlightDashboardCache(store=self.key_value_store)

    @cached_property
    def recommendation_service(self):
        return RecommendationService(
            self.favorite_repository,
            self.highlight_repository,
            self.anime_api_client,
            self.recommendation_cache,
        )

    @cached_property
    def watch_source_sync_service(self):
        return WatchSourceSyncService(
            self.watch_repository,
            [
                self.kodik_client,
                self.anilibria_client,
                self.youtube_client,
                self.justwatch_client,
            ],
        )

    @cached_property
    def password_service(self):
        return PasswordService()

    @cached_property
    def jwt_service(self):
        return JWTService()

    @cached_property
    def token_blocklist(self):
        return TokenBlocklist(self.key_value_store)

    @cached_property
    def rate_limiter(self):
        return RateLimiter(self.key_value_store)

    @cached_property
    def password_reset_mailer(self):
        return PasswordResetMailer()

    def register_user_use_case(self):
        return RegisterUserUseCase(
            self.user_repository, self.password_service
        )

    def login_user_use_case(self):
        return LoginUserUseCase(
            self.user_repository, self.password_service
        )

    def logout_user_use_case(self):
        return LogoutUserUseCase(self.user_repository)

    def update_user_profile_use_case(self):
        return UpdateUserProfileUseCase(
            self.user_repository
        )

    def request_password_reset_use_case(self):
        return RequestPasswordResetUseCase(
            self.user_repository, self.jwt_service, self.password_reset_mailer
        )

    def reset_password_use_case(self):
        return ResetPasswordUseCase(
            self.user_repository, self.jwt_service, self.password_service
        )

    def create_highlight_use_case(self):
        return CreateHighlightUseCase(
            self.highlight_repository,
            self.recommendation_service,
            self.highlight_dashboard_cache,
        )

    def delete_highlight_use_case(self):
        return DeleteHighlightUseCase(
            self.highlight_repository,
            self.recommendation_service,
            self.highlight_dashboard_cache,
        )

    def edit_highlight_use_case(self):
        return EditHighlightUseCase(
            self.highlight_repository,
            self.recommendation_service,
            self.highlight_dashboard_cache,
        )

    def get_user_highlights_use_case(self):
        return GetUserHighlightsUseCase(
            self.highlight_repository, self.anime_api_client
        )

    def get_public_top_highlights_use_case(self):
        return GetPublicTopHighlightsUseCase(
            self.highlight_repository,
            self.anime_api_client,
            self.highlight_dashboard_cache,
        )

    def add_favorite_use_case(self):
        return AddFavoriteUseCase(
            self.favorite_repository,
            self.recommendation_service,
        )

    def remove_favorite_use_case(self):
        return RemoveFavoriteUseCase(
            self.favorite_repository,
            self.recommendation_service,
        )

    def get_favorites_use_case(self):
        return GetFavoritesUseCase(
            self.favorite_repository, self.anime_api_client
        )

    def search_anime_use_case(self):
        return SearchAnimeUseCase(self.anime_api_client)

    def search_anime_by_description_use_case(self):
        return SearchAnimeByDescriptionUseCase(
            self.anime_api_client, self.hf_llm_client
        )

    def autocomplete_anime_use_case(self):
        return AutocompleteAnimeUseCase(
            self.anime_api_client
        )

    def get_season_popular_use_case(self):
        return GetSeasonPopularUseCase(
            self.anime_api_client
        )

    def generate_recommendations_use_case(self):
        return GenerateRecommendationsUseCase(
            self.recommendation_service
        )

    def refresh_recommendations_use_case(self):
        return RefreshRecommendationsUseCase(
            self.recommendation_service
        )

    def get_watch_page_use_case(self):
        return GetWatchPageUseCase(
            self.watch_repository,
            self.highlight_repository,
            self.anime_api_client,
            self.watch_source_sync_service,
        )

    def sync_watch_sources_use_case(self):
        return SyncWatchSourcesUseCase(
            self.anime_api_client,
            self.watch_source_sync_service,
        )

    def upsert_user_anime_status_use_case(self):
        return UpsertUserAnimeStatusUseCase(
            self.watch_repository
        )

    def save_viewing_session_use_case(self):
        return SaveViewingSessionUseCase(
            self.watch_repository
        )

    def create_watch_highlight_use_case(self):
        return CreateWatchHighlightUseCase(
            self.create_highlight_use_case(),
            self.watch_repository,
        )


container = Container()
