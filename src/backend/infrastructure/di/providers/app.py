"""Application-wide singleton providers (caches, clients, security services)."""

from __future__ import annotations

from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

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
from backend.infrastructure.media_proxy import MediaProxyClient
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
    async def media_proxy_client(self) -> AsyncIterator[MediaProxyClient]:
        """Provide the media proxy client.

        Yields:
            MediaProxyClient: Configured proxy client.
        """
        client = MediaProxyClient()
        yield client
        await client.aclose()

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
