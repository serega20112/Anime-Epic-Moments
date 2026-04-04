"""
Application container with shared infrastructure singletons and request-scoped services.
"""

from __future__ import annotations

from functools import cached_property
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.dependencies.settings import Settings
from src.backend.infrastructure.cache.highlight_dashboard_cache import (
    HighlightDashboardCache,
)
from src.backend.infrastructure.cache.key_value_store import KeyValueStore
from src.backend.infrastructure.cache.profile_overview_cache import (
    ProfileOverviewCache,
)
from src.backend.infrastructure.cache.recommendation_cache import RecommendationCache
from src.backend.infrastructure.external.anilibria_client import AniLibriaClient
from src.backend.infrastructure.external.anime_api_client import AnimeApiClient
from src.backend.infrastructure.external.email_verification_mailer import (
    EmailVerificationMailer,
)
from src.backend.infrastructure.external.huggingface_llm_client import (
    HuggingFaceLLMClient,
)
from src.backend.infrastructure.external.justwatch_client import JustWatchClient
from src.backend.infrastructure.external.kodik_client import KodikClient
from src.backend.infrastructure.external.password_reset_mailer import (
    PasswordResetMailer,
)
from src.backend.infrastructure.external.support_email_mailer import (
    SupportEmailMailer,
)
from src.backend.infrastructure.external.telegram_support_notifier import (
    TelegramSupportNotifier,
)
from src.backend.infrastructure.external.youtube_client import YouTubeClient
from src.backend.infrastructure.repositories.collection_repository import (
    CollectionRepository,
)
from src.backend.infrastructure.repositories.favorite_repository import (
    FavoriteRepository,
)
from src.backend.infrastructure.repositories.highlight_repository import (
    HighlightRepository,
)
from src.backend.infrastructure.repositories.support_repository import (
    SupportRepository,
)
from src.backend.infrastructure.repositories.user_repository import UserRepository
from src.backend.infrastructure.repositories.watch_repository import WatchRepository
from src.backend.infrastructure.security.email_verification_store import (
    EmailVerificationStore,
)
from src.backend.infrastructure.security.jwt_service import JWTService
from src.backend.infrastructure.security.password_service import PasswordService
from src.backend.infrastructure.security.rate_limiter import RateLimiter
from src.backend.infrastructure.security.token_blocklist import TokenBlocklist
from src.backend.services.recommendation_service import RecommendationService
from src.backend.services.watch_source_sync_service import WatchSourceSyncService
from src.backend.use_case.anime.autocomplete_anime import AutocompleteAnimeUseCase
from src.backend.use_case.anime.get_season_popular import GetSeasonPopularUseCase
from src.backend.use_case.anime.search_anime import SearchAnimeUseCase
from src.backend.use_case.anime.search_anime_by_description import (
    SearchAnimeByDescriptionUseCase,
)
from src.backend.use_case.auth.get_profile_overview import GetProfileOverviewUseCase
from src.backend.use_case.auth.login_user import LoginUserUseCase
from src.backend.use_case.auth.logout_user import LogoutUserUseCase
from src.backend.use_case.auth.register_user import RegisterUserUseCase
from src.backend.use_case.auth.request_email_verification import (
    RequestEmailVerificationUseCase,
)
from src.backend.use_case.auth.request_password_reset import RequestPasswordResetUseCase
from src.backend.use_case.auth.resend_email_verification import (
    ResendEmailVerificationUseCase,
)
from src.backend.use_case.auth.reset_password import ResetPasswordUseCase
from src.backend.use_case.auth.update_user_profile import UpdateUserProfileUseCase
from src.backend.use_case.auth.verify_email import VerifyEmailUseCase
from src.backend.use_case.collection.add_collection_item import AddCollectionItemUseCase
from src.backend.use_case.collection.create_collection import CreateCollectionUseCase
from src.backend.use_case.collection.get_shared_collection import (
    GetSharedCollectionUseCase,
)
from src.backend.use_case.collection.get_user_collections import (
    GetUserCollectionsUseCase,
)
from src.backend.use_case.collection.remove_collection_item import (
    RemoveCollectionItemUseCase,
)
from src.backend.use_case.favorite.add_favorite import AddFavoriteUseCase
from src.backend.use_case.favorite.get_favorites import GetFavoritesUseCase
from src.backend.use_case.favorite.remove_favorite import RemoveFavoriteUseCase
from src.backend.use_case.highlight.add_highlight_comment import (
    AddHighlightCommentUseCase,
)
from src.backend.use_case.highlight.create_highlight import CreateHighlightUseCase
from src.backend.use_case.highlight.delete_highlight import DeleteHighlightUseCase
from src.backend.use_case.highlight.edit_highlight import EditHighlightUseCase
from src.backend.use_case.highlight.get_highlight_comments import (
    GetHighlightCommentsUseCase,
)
from src.backend.use_case.highlight.get_highlight_feed import GetHighlightFeedUseCase
from src.backend.use_case.highlight.get_highlight_likers import GetHighlightLikersUseCase
from src.backend.use_case.highlight.get_highlight_notifications import (
    GetHighlightNotificationsUseCase,
)
from src.backend.use_case.highlight.get_liked_highlights import (
    GetLikedHighlightsUseCase,
)
from src.backend.use_case.highlight.get_public_top_highlights import (
    GetPublicTopHighlightsUseCase,
)
from src.backend.use_case.highlight.get_saved_highlights import (
    GetSavedHighlightsUseCase,
)
from src.backend.use_case.highlight.get_shared_highlight import (
    GetSharedHighlightUseCase,
)
from src.backend.use_case.highlight.get_user_highlights import GetUserHighlightsUseCase
from src.backend.use_case.highlight.set_highlight_like import SetHighlightLikeUseCase
from src.backend.use_case.highlight.set_saved_highlight import SetSavedHighlightUseCase
from src.backend.use_case.recommendation.ask_ai_recommendations import (
    AskAiRecommendationsUseCase,
)
from src.backend.use_case.recommendation.generate_recommendations import (
    GenerateRecommendationsUseCase,
)
from src.backend.use_case.recommendation.refresh_recommendations import (
    RefreshRecommendationsUseCase,
)
from src.backend.use_case.support.create_support_ticket import (
    CreateSupportTicketUseCase,
)
from src.backend.use_case.user.get_following_highlights import (
    GetFollowingHighlightsUseCase,
)
from src.backend.use_case.user.get_public_profile_overview import (
    GetPublicProfileOverviewUseCase,
)
from src.backend.use_case.user.set_user_follow import SetUserFollowUseCase
from src.backend.use_case.watch.add_anime_comment import AddAnimeCommentUseCase
from src.backend.use_case.watch.add_watch_source import AddWatchSourceUseCase
from src.backend.use_case.watch.create_watch_highlight import (
    CreateWatchHighlightUseCase,
)
from src.backend.use_case.watch.get_anime_discussion import GetAnimeDiscussionUseCase
from src.backend.use_case.watch.get_watch_page import GetWatchPageUseCase
from src.backend.use_case.watch.save_viewing_session import SaveViewingSessionUseCase
from src.backend.use_case.watch.set_anime_comment_like import (
    SetAnimeCommentLikeUseCase,
)
from src.backend.use_case.watch.sync_watch_sources import SyncWatchSourcesUseCase
from src.backend.use_case.watch.upsert_user_anime_status import (
    UpsertUserAnimeStatusUseCase,
)


class Container:
    """Shared process-wide infrastructure."""

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
            print("! HF_TOKEN not configured: description search will use fallback mode")
        return HuggingFaceLLMClient(
            api_key=Settings.hf_token,
            model=Settings.hf_model,
            provider=Settings.hf_provider,
            api_url=Settings.hf_api_url,
        )

    @cached_property
    def recommendation_cache(self):
        return RecommendationCache(store=self.key_value_store)

    @cached_property
    def highlight_dashboard_cache(self):
        return HighlightDashboardCache(store=self.key_value_store)

    @cached_property
    def profile_overview_cache(self):
        return ProfileOverviewCache(store=self.key_value_store)

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

    @cached_property
    def email_verification_mailer(self):
        return EmailVerificationMailer()

    @cached_property
    def telegram_support_notifier(self):
        return TelegramSupportNotifier()

    @cached_property
    def support_email_mailer(self):
        return SupportEmailMailer()

    @cached_property
    def email_verification_store(self):
        return EmailVerificationStore(
            store=self.key_value_store,
            ttl_seconds=Settings.email_verification_expire_minutes * 60,
        )

    def scope(
        self,
        session: AsyncSession | None = None,
        *,
        session_factory: Callable[[], AsyncSession] | None = None,
        request_state=None,
    ) -> "RequestContainer":
        return RequestContainer(
            root=self,
            session=session,
            session_factory=session_factory,
            request_state=request_state,
        )

    async def shutdown(self):
        await self.key_value_store.close()


class RequestContainer:
    """Request-scoped repositories and application services."""

    def __init__(
        self,
        root: Container,
        session: AsyncSession | None = None,
        *,
        session_factory: Callable[[], AsyncSession] | None = None,
        request_state=None,
    ):
        self.root = root
        self._session = session
        self._session_factory = session_factory
        self._request_state = request_state

    @property
    def db_session(self) -> AsyncSession | None:
        return self._session

    @property
    def session(self) -> AsyncSession:
        return self._ensure_session()

    def _ensure_session(self) -> AsyncSession:
        if self._session is not None:
            return self._session
        if self._session_factory is None:
            raise RuntimeError("Request session factory is not configured")
        self._session = self._session_factory()
        if self._request_state is not None:
            self._request_state.db_session = self._session
        return self._session

    async def aclose(self):
        if self._session is None:
            return
        await self._session.close()
        self._session = None
        if self._request_state is not None:
            self._request_state.db_session = None

    @cached_property
    def user_repository(self):
        return UserRepository(self.session)

    @cached_property
    def highlight_repository(self):
        return HighlightRepository(self.session)

    @cached_property
    def favorite_repository(self):
        return FavoriteRepository(self.session)

    @cached_property
    def collection_repository(self):
        return CollectionRepository(self.session)

    @cached_property
    def watch_repository(self):
        return WatchRepository(self.session)

    @cached_property
    def support_repository(self):
        return SupportRepository(self.session)

    @cached_property
    def recommendation_service(self):
        return RecommendationService(
            self.favorite_repository,
            self.highlight_repository,
            self.root.anime_api_client,
            self.root.recommendation_cache,
        )

    @cached_property
    def watch_source_sync_service(self):
        return WatchSourceSyncService(
            self.watch_repository,
            [
                self.root.kodik_client,
                self.root.anilibria_client,
                self.root.youtube_client,
                self.root.justwatch_client,
            ],
        )

    @property
    def password_service(self):
        return self.root.password_service

    @property
    def jwt_service(self):
        return self.root.jwt_service

    @property
    def token_blocklist(self):
        return self.root.token_blocklist

    @property
    def rate_limiter(self):
        return self.root.rate_limiter

    def register_user_use_case(self):
        return RegisterUserUseCase(self.user_repository, self.password_service)

    def request_email_verification_use_case(self):
        return RequestEmailVerificationUseCase(
            self.user_repository,
            self.password_service,
            self.root.email_verification_store,
            self.root.email_verification_mailer,
        )

    def resend_email_verification_use_case(self):
        return ResendEmailVerificationUseCase(
            self.root.email_verification_store,
            self.root.email_verification_mailer,
        )

    def verify_email_use_case(self):
        return VerifyEmailUseCase(
            self.user_repository,
            self.root.email_verification_store,
        )

    def login_user_use_case(self):
        return LoginUserUseCase(self.user_repository, self.password_service)

    def logout_user_use_case(self):
        return LogoutUserUseCase(self.user_repository)

    def update_user_profile_use_case(self):
        return UpdateUserProfileUseCase(
            self.user_repository,
            self.root.profile_overview_cache,
        )

    def get_profile_overview_use_case(self):
        return GetProfileOverviewUseCase(
            self.user_repository,
            self.highlight_repository,
            self.root.anime_api_client,
            self.favorite_repository,
            self.watch_repository,
            self.root.hf_llm_client,
            self.root.profile_overview_cache,
        )

    def request_password_reset_use_case(self):
        return RequestPasswordResetUseCase(
            self.user_repository,
            self.jwt_service,
            self.root.password_reset_mailer,
        )

    def reset_password_use_case(self):
        return ResetPasswordUseCase(
            self.user_repository,
            self.jwt_service,
            self.password_service,
        )

    def create_highlight_use_case(self):
        return CreateHighlightUseCase(
            self.highlight_repository,
            self.recommendation_service,
            self.root.highlight_dashboard_cache,
            self.root.profile_overview_cache,
        )

    def delete_highlight_use_case(self):
        return DeleteHighlightUseCase(
            self.highlight_repository,
            self.recommendation_service,
            self.root.highlight_dashboard_cache,
            self.root.profile_overview_cache,
        )

    def edit_highlight_use_case(self):
        return EditHighlightUseCase(
            self.highlight_repository,
            self.recommendation_service,
            self.root.highlight_dashboard_cache,
            self.root.profile_overview_cache,
        )

    def get_user_highlights_use_case(self):
        return GetUserHighlightsUseCase(
            self.highlight_repository,
            self.root.anime_api_client,
            self.user_repository,
        )

    def get_public_top_highlights_use_case(self):
        return GetPublicTopHighlightsUseCase(
            self.highlight_repository,
            self.root.anime_api_client,
            self.root.highlight_dashboard_cache,
            self.user_repository,
        )

    def get_saved_highlights_use_case(self):
        return GetSavedHighlightsUseCase(
            self.highlight_repository,
            self.root.anime_api_client,
            self.user_repository,
        )

    def get_liked_highlights_use_case(self):
        return GetLikedHighlightsUseCase(
            self.highlight_repository,
            self.root.anime_api_client,
            self.user_repository,
        )

    def get_shared_highlight_use_case(self):
        return GetSharedHighlightUseCase(
            self.highlight_repository,
            self.root.anime_api_client,
            self.user_repository,
        )

    def get_highlight_feed_use_case(self):
        return GetHighlightFeedUseCase(
            self.highlight_repository,
            self.root.anime_api_client,
            self.favorite_repository,
            self.user_repository,
        )

    def get_following_highlights_use_case(self):
        return GetFollowingHighlightsUseCase(
            self.highlight_repository,
            self.root.anime_api_client,
            self.user_repository,
        )

    def set_user_follow_use_case(self):
        return SetUserFollowUseCase(
            self.user_repository,
            self.root.profile_overview_cache,
        )

    def get_public_profile_overview_use_case(self):
        return GetPublicProfileOverviewUseCase(
            self.get_profile_overview_use_case(),
            self.user_repository,
            self.collection_repository,
        )

    def set_highlight_like_use_case(self):
        return SetHighlightLikeUseCase(
            self.highlight_repository,
            self.root.highlight_dashboard_cache,
            self.root.profile_overview_cache,
        )

    def add_highlight_comment_use_case(self):
        return AddHighlightCommentUseCase(
            self.highlight_repository,
            self.root.highlight_dashboard_cache,
            self.root.profile_overview_cache,
        )

    def get_highlight_comments_use_case(self):
        return GetHighlightCommentsUseCase(self.highlight_repository)

    def get_highlight_likers_use_case(self):
        return GetHighlightLikersUseCase(self.highlight_repository)

    def get_highlight_notifications_use_case(self):
        return GetHighlightNotificationsUseCase(self.highlight_repository)

    def set_saved_highlight_use_case(self):
        return SetSavedHighlightUseCase(
            self.highlight_repository,
            self.root.profile_overview_cache,
        )

    def add_favorite_use_case(self):
        return AddFavoriteUseCase(
            self.favorite_repository,
            self.recommendation_service,
            self.root.profile_overview_cache,
        )

    def remove_favorite_use_case(self):
        return RemoveFavoriteUseCase(
            self.favorite_repository,
            self.recommendation_service,
            self.root.profile_overview_cache,
        )

    def get_favorites_use_case(self):
        return GetFavoritesUseCase(
            self.favorite_repository,
            self.root.anime_api_client,
        )

    def create_collection_use_case(self):
        return CreateCollectionUseCase(self.collection_repository)

    def add_collection_item_use_case(self):
        return AddCollectionItemUseCase(self.collection_repository)

    def remove_collection_item_use_case(self):
        return RemoveCollectionItemUseCase(self.collection_repository)

    def get_user_collections_use_case(self):
        return GetUserCollectionsUseCase(self.collection_repository)

    def get_shared_collection_use_case(self):
        return GetSharedCollectionUseCase(self.collection_repository)

    def search_anime_use_case(self):
        return SearchAnimeUseCase(self.root.anime_api_client)

    def search_anime_by_description_use_case(self):
        return SearchAnimeByDescriptionUseCase(
            self.root.anime_api_client,
            self.root.hf_llm_client,
        )

    def autocomplete_anime_use_case(self):
        return AutocompleteAnimeUseCase(self.root.anime_api_client)

    def get_season_popular_use_case(self):
        return GetSeasonPopularUseCase(self.root.anime_api_client)

    def generate_recommendations_use_case(self):
        return GenerateRecommendationsUseCase(self.recommendation_service)

    def ask_ai_recommendations_use_case(self):
        return AskAiRecommendationsUseCase(
            self.favorite_repository,
            self.root.anime_api_client,
            self.root.hf_llm_client,
        )

    def refresh_recommendations_use_case(self):
        return RefreshRecommendationsUseCase(self.recommendation_service)

    def create_support_ticket_use_case(self):
        return CreateSupportTicketUseCase(
            self.support_repository,
            self.root.telegram_support_notifier,
            self.root.support_email_mailer,
        )

    def get_watch_page_use_case(self):
        return GetWatchPageUseCase(
            self.watch_repository,
            self.highlight_repository,
            self.root.anime_api_client,
            self.watch_source_sync_service,
        )

    def add_watch_source_use_case(self):
        return AddWatchSourceUseCase(self.watch_repository)

    def sync_watch_sources_use_case(self):
        return SyncWatchSourcesUseCase(
            self.root.anime_api_client,
            self.watch_source_sync_service,
        )

    def upsert_user_anime_status_use_case(self):
        return UpsertUserAnimeStatusUseCase(
            self.watch_repository,
            self.root.profile_overview_cache,
        )

    def save_viewing_session_use_case(self):
        return SaveViewingSessionUseCase(
            self.watch_repository,
            self.root.profile_overview_cache,
        )

    def add_anime_comment_use_case(self):
        return AddAnimeCommentUseCase(self.watch_repository)

    def get_anime_discussion_use_case(self):
        return GetAnimeDiscussionUseCase(self.watch_repository)

    def set_anime_comment_like_use_case(self):
        return SetAnimeCommentLikeUseCase(self.watch_repository)

    def create_watch_highlight_use_case(self):
        return CreateWatchHighlightUseCase(
            self.create_highlight_use_case(),
            self.watch_repository,
        )


container = Container()
