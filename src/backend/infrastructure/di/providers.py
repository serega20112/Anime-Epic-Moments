"""Dishka providers for all application dependencies."""

from __future__ import annotations

from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.services import WatchSourceSyncService
from backend.application.services.recommendation_service import RecommendationService
from backend.application.use_cases import (
    AddAnimeCommentUseCase,
    AddCollectionItemUseCase,
    AddWatchSourceUseCase,
    AskAiRecommendationsUseCase,
    CreateSupportTicketUseCase,
    DeleteHighlightUseCase,
    GenerateRecommendationsUseCase,
    GetAnimeDiscussionUseCase,
    GetFavoritesUseCase,
    GetLikedHighlightsUseCase,
    GetProfileOverviewUseCase,
    GetPublicProfileOverviewUseCase,
    GetPublicTopHighlightsUseCase,
    GetSeasonPopularUseCase,
    GetUserCollectionsUseCase,
    GetWatchPageUseCase,
    LogoutUserUseCase,
    RefreshRecommendationsUseCase,
    RefreshSessionUseCase,
    RegisterUserUseCase,
    RemoveCollectionItemUseCase,
    RequestEmailVerificationUseCase,
    RequestPasswordResetUseCase,
    ResendEmailVerificationUseCase,
    SearchAnimeUseCase,
    SetAnimeCommentLikeUseCase,
    SetHighlightLikeUseCase,
    SetUserFollowUseCase,
    SyncWatchSourcesUseCase,
    UpdateUserProfileUseCase,
    UpsertUserAnimeStatusUseCase,
    VerifyEmailUseCase,
)
from backend.application.use_cases.anime.autocomplete_anime import AutocompleteAnimeUseCase
from backend.application.use_cases.anime.get_home_page import GetHomePageUseCase
from backend.application.use_cases.anime.search_anime_by_description import (
    SearchAnimeByDescriptionUseCase,
)
from backend.application.use_cases.auth.login_user import LoginUserUseCase
from backend.application.use_cases.auth.reset_password import ResetPasswordUseCase
from backend.application.use_cases.collection.create_collection import CreateCollectionUseCase
from backend.application.use_cases.collection.get_shared_collection import (
    GetSharedCollectionUseCase,
)
from backend.application.use_cases.favorite.add_favorite import AddFavoriteUseCase
from backend.application.use_cases.favorite.remove_favorite import RemoveFavoriteUseCase
from backend.application.use_cases.highlight.add_highlight_comment import (
    AddHighlightCommentUseCase,
)
from backend.application.use_cases.highlight.create_highlight import CreateHighlightUseCase
from backend.application.use_cases.highlight.edit_highlight import EditHighlightUseCase
from backend.application.use_cases.highlight.get_highlight_comments import (
    GetHighlightCommentsUseCase,
)
from backend.application.use_cases.highlight.get_highlight_feed import GetHighlightFeedUseCase
from backend.application.use_cases.highlight.get_highlight_likers import GetHighlightLikersUseCase
from backend.application.use_cases.highlight.get_highlight_notifications import (
    GetHighlightNotificationsUseCase,
)
from backend.application.use_cases.highlight.get_saved_highlights import (
    GetSavedHighlightsUseCase,
)
from backend.application.use_cases.highlight.get_shared_highlight import (
    GetSharedHighlightUseCase,
)
from backend.application.use_cases.highlight.get_user_highlights import GetUserHighlightsUseCase
from backend.application.use_cases.highlight.set_saved_highlight import SetSavedHighlightUseCase
from backend.application.use_cases.user.get_following_highlights import (
    GetFollowingHighlightsUseCase,
)
from backend.application.use_cases.watch.create_watch_highlight import (
    CreateWatchHighlightUseCase,
)
from backend.application.use_cases.watch.save_viewing_session import SaveViewingSessionUseCase
from backend.config import Settings
from backend.infrastructure.cache import HighlightDashboardCache, RecommendationCache
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from backend.infrastructure.external import (
    AniLibriaClient,
    AnimeApiClient,
    JustWatchClient,
    KodikClient,
    PasswordResetMailer,
    SupportEmailMailer,
    TelegramSupportNotifier,
)
from backend.infrastructure.external.email_verification_mailer import EmailVerificationMailer
from backend.infrastructure.external.huggingface_llm_client import HuggingFaceLLMClient
from backend.infrastructure.external.youtube_client import YouTubeClient
from backend.infrastructure.files.database import get_session_factory
from backend.infrastructure.repositories.collection_repository import CollectionRepository
from backend.infrastructure.repositories.favorite_repository import FavoriteRepository
from backend.infrastructure.repositories.highlight_repository import HighlightRepository
from backend.infrastructure.repositories.support_repository import SupportRepository
from backend.infrastructure.repositories.user_repository import UserRepository
from backend.infrastructure.repositories.watch_repository import WatchRepository
from backend.infrastructure.security.account_lock_service import AccountLockService
from backend.infrastructure.security.csrf_service import CSRFService
from backend.infrastructure.security.email_verification_store import EmailVerificationStore
from backend.infrastructure.security.jwt_service import JWTService
from backend.infrastructure.security.password_service import PasswordService
from backend.infrastructure.security.rate_limiter import RateLimiter
from backend.infrastructure.security.token_blocklist import TokenBlocklist


class AppProvider(Provider):
    """Provide application-wide singletons."""

    @provide(scope=Scope.APP)
    def key_value_store(self) -> KeyValueStore:
        """Provide the key-value store.

        Returns:
            KeyValueStore: Redis-backed store with in-memory fallback.
        """
        return KeyValueStore(
            redis_url=Settings.redis_url,
            namespace="anime_epic_moments",
            required=Settings.redis_required,
        )

    @provide(scope=Scope.APP)
    async def anime_api_client(self, store: KeyValueStore) -> AsyncIterator[AnimeApiClient]:
        """Provide the anime API client.

        Args:
            store: Key-value store.

        Yields:
            AnimeApiClient: Configured client.
        """
        client = AnimeApiClient(store=store)
        yield client
        await client.aclose()

    @provide(scope=Scope.APP)
    def kodik_client(self) -> KodikClient:
        """Provide the Kodik client.

        Returns:
            KodikClient: Configured client.
        """
        return KodikClient()

    @provide(scope=Scope.APP)
    def anilibria_client(self) -> AniLibriaClient:
        """Provide the AniLibria client.

        Returns:
            AniLibriaClient: Configured client.
        """
        return AniLibriaClient()

    @provide(scope=Scope.APP)
    def youtube_client(self) -> YouTubeClient:
        """Provide the YouTube client.

        Returns:
            YouTubeClient: Configured client.
        """
        return YouTubeClient()

    @provide(scope=Scope.APP)
    def justwatch_client(self) -> JustWatchClient:
        """Provide the JustWatch client.

        Returns:
            JustWatchClient: Configured client.
        """
        return JustWatchClient()

    @provide(scope=Scope.APP)
    def hf_llm_client(self) -> HuggingFaceLLMClient:
        """Provide the HuggingFace LLM client.

        Returns:
            HuggingFaceLLMClient: Configured client.
        """
        return HuggingFaceLLMClient(
            api_key=Settings.hf_token,
            model=Settings.hf_model,
            provider=Settings.hf_provider,
            api_url=Settings.hf_api_url,
        )

    @provide(scope=Scope.APP)
    def recommendation_cache(self, store: KeyValueStore) -> RecommendationCache:
        """Provide the recommendation cache.

        Args:
            store: Key-value store.

        Returns:
            RecommendationCache: Configured cache.
        """
        return RecommendationCache(store=store)

    @provide(scope=Scope.APP)
    def highlight_dashboard_cache(self, store: KeyValueStore) -> HighlightDashboardCache:
        """Provide the highlight dashboard cache.

        Args:
            store: Key-value store.

        Returns:
            HighlightDashboardCache: Configured cache.
        """
        return HighlightDashboardCache(store=store)

    @provide(scope=Scope.APP)
    def profile_overview_cache(self, store: KeyValueStore) -> ProfileOverviewCache:
        """Provide the profile overview cache.

        Args:
            store: Key-value store.

        Returns:
            ProfileOverviewCache: Configured cache.
        """
        return ProfileOverviewCache(store=store)

    @provide(scope=Scope.APP)
    def password_service(self) -> PasswordService:
        """Provide the password service.

        Returns:
            PasswordService: Configured service.
        """
        return PasswordService()

    @provide(scope=Scope.APP)
    def jwt_service(self) -> JWTService:
        """Provide the JWT service.

        Returns:
            JWTService: Configured service.
        """
        return JWTService()

    @provide(scope=Scope.APP)
    def token_blocklist(self, store: KeyValueStore) -> TokenBlocklist:
        """Provide the token blocklist.

        Args:
            store: Key-value store.

        Returns:
            TokenBlocklist: Configured blocklist.
        """
        return TokenBlocklist(store)

    @provide(scope=Scope.APP)
    def csrf_service(self) -> CSRFService:
        """Provide the CSRF service.

        Returns:
            CSRFService: Configured service.
        """
        return CSRFService()

    @provide(scope=Scope.APP)
    def account_lock_service(self, store: KeyValueStore) -> AccountLockService:
        """Provide the account lock service.

        Args:
            store: Key-value store.

        Returns:
            AccountLockService: Configured service.
        """
        return AccountLockService(store=store)

    @provide(scope=Scope.APP)
    def rate_limiter(self, store: KeyValueStore) -> RateLimiter:
        """Provide the rate limiter.

        Args:
            store: Key-value store.

        Returns:
            RateLimiter: Configured limiter.
        """
        return RateLimiter(store)

    @provide(scope=Scope.APP)
    def password_reset_mailer(self) -> PasswordResetMailer:
        """Provide the password reset mailer.

        Returns:
            PasswordResetMailer: Configured mailer.
        """
        return PasswordResetMailer()

    @provide(scope=Scope.APP)
    def email_verification_mailer(self) -> EmailVerificationMailer:
        """Provide the email verification mailer.

        Returns:
            EmailVerificationMailer: Configured mailer.
        """
        return EmailVerificationMailer()

    @provide(scope=Scope.APP)
    def telegram_support_notifier(self) -> TelegramSupportNotifier:
        """Provide the Telegram support notifier.

        Returns:
            TelegramSupportNotifier: Configured notifier.
        """
        return TelegramSupportNotifier()

    @provide(scope=Scope.APP)
    def support_email_mailer(self) -> SupportEmailMailer:
        """Provide the support email mailer.

        Returns:
            SupportEmailMailer: Configured mailer.
        """
        return SupportEmailMailer()

    @provide(scope=Scope.APP)
    def email_verification_store(self, store: KeyValueStore) -> EmailVerificationStore:
        """Provide the email verification store.

        Args:
            store: Key-value store.

        Returns:
            EmailVerificationStore: Configured store.
        """
        return EmailVerificationStore(
            store=store,
            ttl_seconds=Settings.email_verification_expire_minutes * 60,
        )


class RequestProvider(Provider):
    """Provide request-scoped repositories and services."""

    @provide(scope=Scope.REQUEST)
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Provide an async database session.

        Yields:
            AsyncSession: Database session.
        """
        factory = get_session_factory()
        async with factory() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def user_repository(self, session: AsyncSession) -> UserRepository:
        """Provide the user repository.

        Args:
            session: Database session.

        Returns:
            UserRepository: Configured repository.
        """
        return UserRepository(session)

    @provide(scope=Scope.REQUEST)
    def highlight_repository(self, session: AsyncSession) -> HighlightRepository:
        """Provide the highlight repository.

        Args:
            session: Database session.

        Returns:
            HighlightRepository: Configured repository.
        """
        return HighlightRepository(session)

    @provide(scope=Scope.REQUEST)
    def favorite_repository(self, session: AsyncSession) -> FavoriteRepository:
        """Provide the favorite repository.

        Args:
            session: Database session.

        Returns:
            FavoriteRepository: Configured repository.
        """
        return FavoriteRepository(session)

    @provide(scope=Scope.REQUEST)
    def collection_repository(self, session: AsyncSession) -> CollectionRepository:
        """Provide the collection repository.

        Args:
            session: Database session.

        Returns:
            CollectionRepository: Configured repository.
        """
        return CollectionRepository(session)

    @provide(scope=Scope.REQUEST)
    def watch_repository(self, session: AsyncSession) -> WatchRepository:
        """Provide the watch repository.

        Args:
            session: Database session.

        Returns:
            WatchRepository: Configured repository.
        """
        return WatchRepository(session)

    @provide(scope=Scope.REQUEST)
    def support_repository(self, session: AsyncSession) -> SupportRepository:
        """Provide the support repository.

        Args:
            session: Database session.

        Returns:
            SupportRepository: Configured repository.
        """
        return SupportRepository(session)

    @provide(scope=Scope.REQUEST)
    def recommendation_service(
        self,
        favorite_repository: FavoriteRepository,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        recommendation_cache: RecommendationCache,
    ) -> RecommendationService:
        """Provide the recommendation service.

        Args:
            favorite_repository: Favorite repository.
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            recommendation_cache: Recommendation cache.

        Returns:
            RecommendationService: Configured service.
        """
        return RecommendationService(
            favorite_repository,
            highlight_repository,
            anime_api_client,
            recommendation_cache,
        )

    @provide(scope=Scope.REQUEST)
    def watch_source_sync_service(
        self,
        watch_repository: WatchRepository,
        kodik_client: KodikClient,
        anilibria_client: AniLibriaClient,
        youtube_client: YouTubeClient,
        justwatch_client: JustWatchClient,
    ) -> WatchSourceSyncService:
        """Provide the watch source sync service.

        Args:
            watch_repository: Watch repository.
            kodik_client: Kodik client.
            anilibria_client: AniLibria client.
            youtube_client: YouTube client.
            justwatch_client: JustWatch client.

        Returns:
            WatchSourceSyncService: Configured service.
        """
        return WatchSourceSyncService(
            watch_repository,
            [
                kodik_client,
                anilibria_client,
                youtube_client,
                justwatch_client,
            ],
        )


class UseCaseProvider(Provider):
    """Provide all application use cases."""

    @provide(scope=Scope.REQUEST)
    def register_user(
        self,
        user_repository: UserRepository,
        password_service: PasswordService,
    ) -> RegisterUserUseCase:
        """Provide the register user use case.

        Args:
            user_repository: User repository.
            password_service: Password service.

        Returns:
            RegisterUserUseCase: Configured use case.
        """
        return RegisterUserUseCase(user_repository, password_service)

    @provide(scope=Scope.REQUEST)
    def request_email_verification(
        self,
        user_repository: UserRepository,
        password_service: PasswordService,
        email_verification_store: EmailVerificationStore,
        email_verification_mailer: EmailVerificationMailer,
    ) -> RequestEmailVerificationUseCase:
        """Provide the request email verification use case.

        Args:
            user_repository: User repository.
            password_service: Password service.
            email_verification_store: Verification store.
            email_verification_mailer: Verification mailer.

        Returns:
            RequestEmailVerificationUseCase: Configured use case.
        """
        return RequestEmailVerificationUseCase(
            user_repository,
            password_service,
            email_verification_store,
            email_verification_mailer,
        )

    @provide(scope=Scope.REQUEST)
    def resend_email_verification(
        self,
        email_verification_store: EmailVerificationStore,
        email_verification_mailer: EmailVerificationMailer,
    ) -> ResendEmailVerificationUseCase:
        """Provide the resend email verification use case.

        Args:
            email_verification_store: Verification store.
            email_verification_mailer: Verification mailer.

        Returns:
            ResendEmailVerificationUseCase: Configured use case.
        """
        return ResendEmailVerificationUseCase(
            email_verification_store,
            email_verification_mailer,
        )

    @provide(scope=Scope.REQUEST)
    def verify_email(
        self,
        user_repository: UserRepository,
        email_verification_store: EmailVerificationStore,
    ) -> VerifyEmailUseCase:
        """Provide the verify email use case.

        Args:
            user_repository: User repository.
            email_verification_store: Verification store.

        Returns:
            VerifyEmailUseCase: Configured use case.
        """
        return VerifyEmailUseCase(user_repository, email_verification_store)

    @provide(scope=Scope.REQUEST)
    def login_user(
        self,
        user_repository: UserRepository,
        password_service: PasswordService,
        account_lock_service: AccountLockService,
    ) -> LoginUserUseCase:
        """Provide the login user use case.

        Args:
            user_repository: User repository.
            password_service: Password service.
            account_lock_service: Account lockout service.

        Returns:
            LoginUserUseCase: Configured use case.
        """
        return LoginUserUseCase(user_repository, password_service, account_lock_service)

    @provide(scope=Scope.REQUEST)
    def logout_user(
        self,
        jwt_service: JWTService,
        token_blocklist: TokenBlocklist,
    ) -> LogoutUserUseCase:
        """Provide the logout user use case.

        Args:
            jwt_service: JWT service.
            token_blocklist: Token blocklist.

        Returns:
            LogoutUserUseCase: Configured use case.
        """
        return LogoutUserUseCase(jwt_service, token_blocklist)

    @provide(scope=Scope.REQUEST)
    def refresh_session(
        self,
        jwt_service: JWTService,
        token_blocklist: TokenBlocklist,
    ) -> RefreshSessionUseCase:
        """Provide the refresh session use case.

        Args:
            jwt_service: JWT service.
            token_blocklist: Token blocklist.

        Returns:
            RefreshSessionUseCase: Configured use case.
        """
        return RefreshSessionUseCase(jwt_service, token_blocklist)

    @provide(scope=Scope.REQUEST)
    def update_user_profile(
        self,
        user_repository: UserRepository,
        profile_overview_cache: ProfileOverviewCache,
    ) -> UpdateUserProfileUseCase:
        """Provide the update user profile use case.

        Args:
            user_repository: User repository.
            profile_overview_cache: Profile overview cache.

        Returns:
            UpdateUserProfileUseCase: Configured use case.
        """
        return UpdateUserProfileUseCase(user_repository, profile_overview_cache)

    @provide(scope=Scope.REQUEST)
    def get_profile_overview(
        self,
        user_repository: UserRepository,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        favorite_repository: FavoriteRepository,
        watch_repository: WatchRepository,
        hf_llm_client: HuggingFaceLLMClient,
        profile_overview_cache: ProfileOverviewCache,
    ) -> GetProfileOverviewUseCase:
        """Provide the get profile overview use case.

        Args:
            user_repository: User repository.
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            favorite_repository: Favorite repository.
            watch_repository: Watch repository.
            hf_llm_client: LLM client.
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
            hf_llm_client,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    def request_password_reset(
        self,
        user_repository: UserRepository,
        jwt_service: JWTService,
        password_reset_mailer: PasswordResetMailer,
    ) -> RequestPasswordResetUseCase:
        """Provide the request password reset use case.

        Args:
            user_repository: User repository.
            jwt_service: JWT service.
            password_reset_mailer: Password reset mailer.

        Returns:
            RequestPasswordResetUseCase: Configured use case.
        """
        return RequestPasswordResetUseCase(
            user_repository,
            jwt_service,
            password_reset_mailer,
        )

    @provide(scope=Scope.REQUEST)
    def reset_password(
        self,
        user_repository: UserRepository,
        jwt_service: JWTService,
        password_service: PasswordService,
        token_blocklist: TokenBlocklist,
    ) -> ResetPasswordUseCase:
        """Provide the reset password use case.

        Args:
            user_repository: User repository.
            jwt_service: JWT service.
            password_service: Password service.
            token_blocklist: Token blocklist.

        Returns:
            ResetPasswordUseCase: Configured use case.
        """
        return ResetPasswordUseCase(user_repository, jwt_service, password_service, token_blocklist)

    @provide(scope=Scope.REQUEST)
    def create_highlight(
        self,
        highlight_repository: HighlightRepository,
        recommendation_service: RecommendationService,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
    ) -> CreateHighlightUseCase:
        """Provide the create highlight use case.

        Args:
            highlight_repository: Highlight repository.
            recommendation_service: Recommendation service.
            highlight_dashboard_cache: Dashboard cache.
            profile_overview_cache: Profile overview cache.

        Returns:
            CreateHighlightUseCase: Configured use case.
        """
        return CreateHighlightUseCase(
            highlight_repository,
            recommendation_service,
            highlight_dashboard_cache,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    def delete_highlight(
        self,
        highlight_repository: HighlightRepository,
        recommendation_service: RecommendationService,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
    ) -> DeleteHighlightUseCase:
        """Provide the delete highlight use case.

        Args:
            highlight_repository: Highlight repository.
            recommendation_service: Recommendation service.
            highlight_dashboard_cache: Dashboard cache.
            profile_overview_cache: Profile overview cache.

        Returns:
            DeleteHighlightUseCase: Configured use case.
        """
        return DeleteHighlightUseCase(
            highlight_repository,
            recommendation_service,
            highlight_dashboard_cache,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    def edit_highlight(
        self,
        highlight_repository: HighlightRepository,
        recommendation_service: RecommendationService,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
    ) -> EditHighlightUseCase:
        """Provide the edit highlight use case.

        Args:
            highlight_repository: Highlight repository.
            recommendation_service: Recommendation service.
            highlight_dashboard_cache: Dashboard cache.
            profile_overview_cache: Profile overview cache.

        Returns:
            EditHighlightUseCase: Configured use case.
        """
        return EditHighlightUseCase(
            highlight_repository,
            recommendation_service,
            highlight_dashboard_cache,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    def get_user_highlights(
        self,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        user_repository: UserRepository,
    ) -> GetUserHighlightsUseCase:
        """Provide the get user highlights use case.

        Args:
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            user_repository: User repository.

        Returns:
            GetUserHighlightsUseCase: Configured use case.
        """
        return GetUserHighlightsUseCase(
            highlight_repository,
            anime_api_client,
            user_repository,
        )

    @provide(scope=Scope.REQUEST)
    def get_public_top_highlights(
        self,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        highlight_dashboard_cache: HighlightDashboardCache,
        user_repository: UserRepository,
    ) -> GetPublicTopHighlightsUseCase:
        """Provide the get public top highlights use case.

        Args:
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            highlight_dashboard_cache: Dashboard cache.
            user_repository: User repository.

        Returns:
            GetPublicTopHighlightsUseCase: Configured use case.
        """
        return GetPublicTopHighlightsUseCase(
            highlight_repository,
            anime_api_client,
            highlight_dashboard_cache,
            user_repository,
        )

    @provide(scope=Scope.REQUEST)
    def get_saved_highlights(
        self,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        user_repository: UserRepository,
    ) -> GetSavedHighlightsUseCase:
        """Provide the get saved highlights use case.

        Args:
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            user_repository: User repository.

        Returns:
            GetSavedHighlightsUseCase: Configured use case.
        """
        return GetSavedHighlightsUseCase(
            highlight_repository,
            anime_api_client,
            user_repository,
        )

    @provide(scope=Scope.REQUEST)
    def get_liked_highlights(
        self,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        user_repository: UserRepository,
    ) -> GetLikedHighlightsUseCase:
        """Provide the get liked highlights use case.

        Args:
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            user_repository: User repository.

        Returns:
            GetLikedHighlightsUseCase: Configured use case.
        """
        return GetLikedHighlightsUseCase(
            highlight_repository,
            anime_api_client,
            user_repository,
        )

    @provide(scope=Scope.REQUEST)
    def get_shared_highlight(
        self,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        user_repository: UserRepository,
    ) -> GetSharedHighlightUseCase:
        """Provide the get shared highlight use case.

        Args:
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            user_repository: User repository.

        Returns:
            GetSharedHighlightUseCase: Configured use case.
        """
        return GetSharedHighlightUseCase(
            highlight_repository,
            anime_api_client,
            user_repository,
        )

    @provide(scope=Scope.REQUEST)
    def get_highlight_feed(
        self,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        favorite_repository: FavoriteRepository,
        user_repository: UserRepository,
    ) -> GetHighlightFeedUseCase:
        """Provide the get highlight feed use case.

        Args:
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            favorite_repository: Favorite repository.
            user_repository: User repository.

        Returns:
            GetHighlightFeedUseCase: Configured use case.
        """
        return GetHighlightFeedUseCase(
            highlight_repository,
            anime_api_client,
            favorite_repository,
            user_repository,
        )

    @provide(scope=Scope.REQUEST)
    def get_following_highlights(
        self,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        user_repository: UserRepository,
    ) -> GetFollowingHighlightsUseCase:
        """Provide the get following highlights use case.

        Args:
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            user_repository: User repository.

        Returns:
            GetFollowingHighlightsUseCase: Configured use case.
        """
        return GetFollowingHighlightsUseCase(
            highlight_repository,
            anime_api_client,
            user_repository,
        )

    @provide(scope=Scope.REQUEST)
    def set_user_follow(
        self,
        user_repository: UserRepository,
        profile_overview_cache: ProfileOverviewCache,
    ) -> SetUserFollowUseCase:
        """Provide the set user follow use case.

        Args:
            user_repository: User repository.
            profile_overview_cache: Profile overview cache.

        Returns:
            SetUserFollowUseCase: Configured use case.
        """
        return SetUserFollowUseCase(user_repository, profile_overview_cache)

    @provide(scope=Scope.REQUEST)
    def get_public_profile_overview(
        self,
        get_profile_overview: GetProfileOverviewUseCase,
        user_repository: UserRepository,
        collection_repository: CollectionRepository,
    ) -> GetPublicProfileOverviewUseCase:
        """Provide the get public profile overview use case.

        Args:
            get_profile_overview: Profile overview use case.
            user_repository: User repository.
            collection_repository: Collection repository.

        Returns:
            GetPublicProfileOverviewUseCase: Configured use case.
        """
        return GetPublicProfileOverviewUseCase(
            get_profile_overview,
            user_repository,
            collection_repository,
        )

    @provide(scope=Scope.REQUEST)
    def set_highlight_like(
        self,
        highlight_repository: HighlightRepository,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
    ) -> SetHighlightLikeUseCase:
        """Provide the set highlight like use case.

        Args:
            highlight_repository: Highlight repository.
            highlight_dashboard_cache: Dashboard cache.
            profile_overview_cache: Profile overview cache.

        Returns:
            SetHighlightLikeUseCase: Configured use case.
        """
        return SetHighlightLikeUseCase(
            highlight_repository,
            highlight_dashboard_cache,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    def add_highlight_comment(
        self,
        highlight_repository: HighlightRepository,
        highlight_dashboard_cache: HighlightDashboardCache,
        profile_overview_cache: ProfileOverviewCache,
    ) -> AddHighlightCommentUseCase:
        """Provide the add highlight comment use case.

        Args:
            highlight_repository: Highlight repository.
            highlight_dashboard_cache: Dashboard cache.
            profile_overview_cache: Profile overview cache.

        Returns:
            AddHighlightCommentUseCase: Configured use case.
        """
        return AddHighlightCommentUseCase(
            highlight_repository,
            highlight_dashboard_cache,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    def get_highlight_comments(
        self,
        highlight_repository: HighlightRepository,
    ) -> GetHighlightCommentsUseCase:
        """Provide the get highlight comments use case.

        Args:
            highlight_repository: Highlight repository.

        Returns:
            GetHighlightCommentsUseCase: Configured use case.
        """
        return GetHighlightCommentsUseCase(highlight_repository)

    @provide(scope=Scope.REQUEST)
    def get_highlight_likers(
        self,
        highlight_repository: HighlightRepository,
    ) -> GetHighlightLikersUseCase:
        """Provide the get highlight likers use case.

        Args:
            highlight_repository: Highlight repository.

        Returns:
            GetHighlightLikersUseCase: Configured use case.
        """
        return GetHighlightLikersUseCase(highlight_repository)

    @provide(scope=Scope.REQUEST)
    def get_highlight_notifications(
        self,
        highlight_repository: HighlightRepository,
    ) -> GetHighlightNotificationsUseCase:
        """Provide the get highlight notifications use case.

        Args:
            highlight_repository: Highlight repository.

        Returns:
            GetHighlightNotificationsUseCase: Configured use case.
        """
        return GetHighlightNotificationsUseCase(highlight_repository)

    @provide(scope=Scope.REQUEST)
    def set_saved_highlight(
        self,
        highlight_repository: HighlightRepository,
        profile_overview_cache: ProfileOverviewCache,
    ) -> SetSavedHighlightUseCase:
        """Provide the set saved highlight use case.

        Args:
            highlight_repository: Highlight repository.
            profile_overview_cache: Profile overview cache.

        Returns:
            SetSavedHighlightUseCase: Configured use case.
        """
        return SetSavedHighlightUseCase(highlight_repository, profile_overview_cache)

    @provide(scope=Scope.REQUEST)
    def add_favorite(
        self,
        favorite_repository: FavoriteRepository,
        recommendation_service: RecommendationService,
        profile_overview_cache: ProfileOverviewCache,
    ) -> AddFavoriteUseCase:
        """Provide the add favorite use case.

        Args:
            favorite_repository: Favorite repository.
            recommendation_service: Recommendation service.
            profile_overview_cache: Profile overview cache.

        Returns:
            AddFavoriteUseCase: Configured use case.
        """
        return AddFavoriteUseCase(
            favorite_repository,
            recommendation_service,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    def remove_favorite(
        self,
        favorite_repository: FavoriteRepository,
        recommendation_service: RecommendationService,
        profile_overview_cache: ProfileOverviewCache,
    ) -> RemoveFavoriteUseCase:
        """Provide the remove favorite use case.

        Args:
            favorite_repository: Favorite repository.
            recommendation_service: Recommendation service.
            profile_overview_cache: Profile overview cache.

        Returns:
            RemoveFavoriteUseCase: Configured use case.
        """
        return RemoveFavoriteUseCase(
            favorite_repository,
            recommendation_service,
            profile_overview_cache,
        )

    @provide(scope=Scope.REQUEST)
    def get_favorites(
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
    def create_collection(
        self,
        collection_repository: CollectionRepository,
    ) -> CreateCollectionUseCase:
        """Provide the create collection use case.

        Args:
            collection_repository: Collection repository.

        Returns:
            CreateCollectionUseCase: Configured use case.
        """
        return CreateCollectionUseCase(collection_repository)

    @provide(scope=Scope.REQUEST)
    def add_collection_item(
        self,
        collection_repository: CollectionRepository,
    ) -> AddCollectionItemUseCase:
        """Provide the add collection item use case.

        Args:
            collection_repository: Collection repository.

        Returns:
            AddCollectionItemUseCase: Configured use case.
        """
        return AddCollectionItemUseCase(collection_repository)

    @provide(scope=Scope.REQUEST)
    def remove_collection_item(
        self,
        collection_repository: CollectionRepository,
    ) -> RemoveCollectionItemUseCase:
        """Provide the remove collection item use case.

        Args:
            collection_repository: Collection repository.

        Returns:
            RemoveCollectionItemUseCase: Configured use case.
        """
        return RemoveCollectionItemUseCase(collection_repository)

    @provide(scope=Scope.REQUEST)
    def get_user_collections(
        self,
        collection_repository: CollectionRepository,
    ) -> GetUserCollectionsUseCase:
        """Provide the get user collections use case.

        Args:
            collection_repository: Collection repository.

        Returns:
            GetUserCollectionsUseCase: Configured use case.
        """
        return GetUserCollectionsUseCase(collection_repository)

    @provide(scope=Scope.REQUEST)
    def get_shared_collection(
        self,
        collection_repository: CollectionRepository,
    ) -> GetSharedCollectionUseCase:
        """Provide the get shared collection use case.

        Args:
            collection_repository: Collection repository.

        Returns:
            GetSharedCollectionUseCase: Configured use case.
        """
        return GetSharedCollectionUseCase(collection_repository)

    @provide(scope=Scope.REQUEST)
    def search_anime(self, anime_api_client: AnimeApiClient) -> SearchAnimeUseCase:
        """Provide the search anime use case.

        Args:
            anime_api_client: Anime API client.

        Returns:
            SearchAnimeUseCase: Configured use case.
        """
        return SearchAnimeUseCase(anime_api_client)

    @provide(scope=Scope.REQUEST)
    def search_anime_by_description(
        self,
        anime_api_client: AnimeApiClient,
        hf_llm_client: HuggingFaceLLMClient,
    ) -> SearchAnimeByDescriptionUseCase:
        """Provide the search by description use case.

        Args:
            anime_api_client: Anime API client.
            hf_llm_client: LLM client.

        Returns:
            SearchAnimeByDescriptionUseCase: Configured use case.
        """
        return SearchAnimeByDescriptionUseCase(anime_api_client, hf_llm_client)

    @provide(scope=Scope.REQUEST)
    def autocomplete_anime(
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
    def get_home_page(self) -> GetHomePageUseCase:
        """Provide the home page use case.

        Returns:
            GetHomePageUseCase: Configured use case.
        """
        return GetHomePageUseCase()

    @provide(scope=Scope.REQUEST)
    def get_season_popular(
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
    def generate_recommendations(
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
    def ask_ai_recommendations(
        self,
        favorite_repository: FavoriteRepository,
        anime_api_client: AnimeApiClient,
        hf_llm_client: HuggingFaceLLMClient,
    ) -> AskAiRecommendationsUseCase:
        """Provide the ask AI recommendations use case.

        Args:
            favorite_repository: Favorite repository.
            anime_api_client: Anime API client.
            hf_llm_client: LLM client.

        Returns:
            AskAiRecommendationsUseCase: Configured use case.
        """
        return AskAiRecommendationsUseCase(
            favorite_repository,
            anime_api_client,
            hf_llm_client,
        )

    @provide(scope=Scope.REQUEST)
    def refresh_recommendations(
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

    @provide(scope=Scope.REQUEST)
    def create_support_ticket(
        self,
        support_repository: SupportRepository,
        telegram_support_notifier: TelegramSupportNotifier,
        support_email_mailer: SupportEmailMailer,
    ) -> CreateSupportTicketUseCase:
        """Provide the create support ticket use case.

        Args:
            support_repository: Support repository.
            telegram_support_notifier: Telegram notifier.
            support_email_mailer: Support email mailer.

        Returns:
            CreateSupportTicketUseCase: Configured use case.
        """
        return CreateSupportTicketUseCase(
            support_repository,
            telegram_support_notifier,
            support_email_mailer,
        )

    @provide(scope=Scope.REQUEST)
    def get_watch_page(
        self,
        watch_repository: WatchRepository,
        highlight_repository: HighlightRepository,
        anime_api_client: AnimeApiClient,
        watch_source_sync_service: WatchSourceSyncService,
    ) -> GetWatchPageUseCase:
        """Provide the get watch page use case.

        Args:
            watch_repository: Watch repository.
            highlight_repository: Highlight repository.
            anime_api_client: Anime API client.
            watch_source_sync_service: Watch source sync service.

        Returns:
            GetWatchPageUseCase: Configured use case.
        """
        return GetWatchPageUseCase(
            watch_repository,
            highlight_repository,
            anime_api_client,
            watch_source_sync_service,
        )

    @provide(scope=Scope.REQUEST)
    def add_watch_source(
        self,
        watch_repository: WatchRepository,
    ) -> AddWatchSourceUseCase:
        """Provide the add watch source use case.

        Args:
            watch_repository: Watch repository.

        Returns:
            AddWatchSourceUseCase: Configured use case.
        """
        return AddWatchSourceUseCase(watch_repository)

    @provide(scope=Scope.REQUEST)
    def sync_watch_sources(
        self,
        anime_api_client: AnimeApiClient,
        watch_source_sync_service: WatchSourceSyncService,
    ) -> SyncWatchSourcesUseCase:
        """Provide the sync watch sources use case.

        Args:
            anime_api_client: Anime API client.
            watch_source_sync_service: Watch source sync service.

        Returns:
            SyncWatchSourcesUseCase: Configured use case.
        """
        return SyncWatchSourcesUseCase(anime_api_client, watch_source_sync_service)

    @provide(scope=Scope.REQUEST)
    def upsert_user_anime_status(
        self,
        watch_repository: WatchRepository,
        profile_overview_cache: ProfileOverviewCache,
    ) -> UpsertUserAnimeStatusUseCase:
        """Provide the upsert user anime status use case.

        Args:
            watch_repository: Watch repository.
            profile_overview_cache: Profile overview cache.

        Returns:
            UpsertUserAnimeStatusUseCase: Configured use case.
        """
        return UpsertUserAnimeStatusUseCase(watch_repository, profile_overview_cache)

    @provide(scope=Scope.REQUEST)
    def save_viewing_session(
        self,
        watch_repository: WatchRepository,
        profile_overview_cache: ProfileOverviewCache,
    ) -> SaveViewingSessionUseCase:
        """Provide the save viewing session use case.

        Args:
            watch_repository: Watch repository.
            profile_overview_cache: Profile overview cache.

        Returns:
            SaveViewingSessionUseCase: Configured use case.
        """
        return SaveViewingSessionUseCase(watch_repository, profile_overview_cache)

    @provide(scope=Scope.REQUEST)
    def add_anime_comment(
        self,
        watch_repository: WatchRepository,
    ) -> AddAnimeCommentUseCase:
        """Provide the add anime comment use case.

        Args:
            watch_repository: Watch repository.

        Returns:
            AddAnimeCommentUseCase: Configured use case.
        """
        return AddAnimeCommentUseCase(watch_repository)

    @provide(scope=Scope.REQUEST)
    def get_anime_discussion(
        self,
        watch_repository: WatchRepository,
    ) -> GetAnimeDiscussionUseCase:
        """Provide the get anime discussion use case.

        Args:
            watch_repository: Watch repository.

        Returns:
            GetAnimeDiscussionUseCase: Configured use case.
        """
        return GetAnimeDiscussionUseCase(watch_repository)

    @provide(scope=Scope.REQUEST)
    def set_anime_comment_like(
        self,
        watch_repository: WatchRepository,
    ) -> SetAnimeCommentLikeUseCase:
        """Provide the set anime comment like use case.

        Args:
            watch_repository: Watch repository.

        Returns:
            SetAnimeCommentLikeUseCase: Configured use case.
        """
        return SetAnimeCommentLikeUseCase(watch_repository)

    @provide(scope=Scope.REQUEST)
    def create_watch_highlight(
        self,
        create_highlight: CreateHighlightUseCase,
        watch_repository: WatchRepository,
    ) -> CreateWatchHighlightUseCase:
        """Provide the create watch highlight use case.

        Args:
            create_highlight: Create highlight use case.
            watch_repository: Watch repository.

        Returns:
            CreateWatchHighlightUseCase: Configured use case.
        """
        return CreateWatchHighlightUseCase(create_highlight, watch_repository)
