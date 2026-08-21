"""Application-wide singleton providers (caches, clients, security services)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from dishka import Provider, Scope, provide

from backend.config import Settings
from backend.infrastructure.cache import HighlightDashboardCache, RecommendationCache
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from backend.infrastructure.external import (
    AniBoomProvider,
    AniLibriaClient,
    AnimeApiClient,
    JustWatchClient,
    KodikClient,
    PasswordResetMailer,
    SamebandProvider,
    SupportEmailMailer,
    TelegramSupportNotifier,
)
from backend.infrastructure.external.email_verification_mailer import EmailVerificationMailer
from backend.infrastructure.external.failover_llm_client import FailoverLLMClient
from backend.infrastructure.external.google_gemini_llm_client import GoogleGeminiLLMClient
from backend.infrastructure.external.huggingface_llm_client import HuggingFaceLLMClient
from backend.infrastructure.external.openrouter_llm_client import OpenRouterLLMClient
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
    async def key_value_store(self) -> AsyncIterator[KeyValueStore]:
        """Provide the key-value store.

        Yields:
            KeyValueStore: Redis-backed store with in-memory fallback.
        """
        store = KeyValueStore(
            redis_url=Settings.redis_url,
            namespace="anime_epic_moments",
            required=Settings.redis_required,
        )
        yield store
        await store.close()

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
    async def kodik_client(self) -> AsyncIterator[KodikClient]:
        """Provide the Kodik client.

        Yields:
            KodikClient: Configured client.
        """
        client = KodikClient()
        yield client
        await client.aclose()

    @provide(scope=Scope.APP)
    async def anilibria_client(self) -> AsyncIterator[AniLibriaClient]:
        """Provide the AniLibria client.

        Yields:
            AniLibriaClient: Configured client.
        """
        client = AniLibriaClient()
        yield client
        await client.aclose()

    @provide(scope=Scope.APP)
    async def youtube_client(self) -> AsyncIterator[YouTubeClient]:
        """Provide the YouTube client.

        Yields:
            YouTubeClient: Configured client.
        """
        client = YouTubeClient()
        yield client
        await client.aclose()

    @provide(scope=Scope.APP)
    async def justwatch_client(self) -> AsyncIterator[JustWatchClient]:
        """Provide the JustWatch client.

        Yields:
            JustWatchClient: Configured client.
        """
        client = JustWatchClient()
        yield client
        await client.aclose()

    @provide(scope=Scope.APP)
    async def sameband_provider(self) -> AsyncIterator[SamebandProvider]:
        """Provide the SameBand provider.

        Yields:
            SamebandProvider: Configured provider.
        """
        provider = SamebandProvider(
            base_url=Settings.sameband_base_url,
            enabled=Settings.sameband_enabled,
            timeout=Settings.sameband_timeout,
        )
        yield provider
        await provider.aclose()

    @provide(scope=Scope.APP)
    async def aniboom_provider(self) -> AsyncIterator[AniBoomProvider]:
        """Provide the AniBoom provider.

        Yields:
            AniBoomProvider: Configured provider.
        """
        provider = AniBoomProvider(
            base_url=Settings.aniboom_base_url,
            enabled=Settings.aniboom_enabled,
            timeout=Settings.aniboom_timeout,
        )
        yield provider
        await provider.aclose()

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
    async def llm_client(self) -> AsyncIterator[FailoverLLMClient]:
        """Provide the LLM client with provider failover chain.

        Priority: OpenRouter (if key configured) -> Google Gemini -> Hugging Face.

        Yields:
            FailoverLLMClient: Failover client for AI-powered search.
        """
        gemini = GoogleGeminiLLMClient(
            api_key=Settings.google_api_key,
            model=Settings.google_model,
            api_url=Settings.google_api_url,
        )
        huggingface = HuggingFaceLLMClient(
            api_key=Settings.hf_token,
            model=Settings.hf_model,
            provider=Settings.hf_provider,
            api_url=Settings.hf_api_url,
        )
        if Settings.openrouter_api_key:
            primary: Any = OpenRouterLLMClient(
                api_key=Settings.openrouter_api_key,
                model=Settings.openrouter_model,
                api_url=Settings.openrouter_api_url,
            )
            fallback = gemini if Settings.google_api_key else huggingface
        elif Settings.google_api_key:
            primary = gemini
            fallback = huggingface
        else:
            primary = gemini
            fallback = huggingface
        client = FailoverLLMClient(primary=primary, fallback=fallback)
        yield client
        await client.aclose()

    @provide(scope=Scope.APP)
    async def recommendation_cache(self, store: KeyValueStore) -> RecommendationCache:
        """Provide the recommendation cache.

        Args:
            store: Key-value store.

        Returns:
            RecommendationCache: Configured cache.
        """
        return RecommendationCache(store=store)

    @provide(scope=Scope.APP)
    async def highlight_dashboard_cache(self, store: KeyValueStore) -> HighlightDashboardCache:
        """Provide the highlight dashboard cache.

        Args:
            store: Key-value store.

        Returns:
            HighlightDashboardCache: Configured cache.
        """
        return HighlightDashboardCache(store=store)

    @provide(scope=Scope.APP)
    async def profile_overview_cache(self, store: KeyValueStore) -> ProfileOverviewCache:
        """Provide the profile overview cache.

        Args:
            store: Key-value store.

        Returns:
            ProfileOverviewCache: Configured cache.
        """
        return ProfileOverviewCache(store=store)

    @provide(scope=Scope.APP)
    async def password_service(self) -> PasswordService:
        """Provide the password service.

        Returns:
            PasswordService: Configured service.
        """
        return PasswordService()

    @provide(scope=Scope.APP)
    async def jwt_service(self) -> JWTService:
        """Provide the JWT service.

        Returns:
            JWTService: Configured service.
        """
        return JWTService()

    @provide(scope=Scope.APP)
    async def token_blocklist(self, store: KeyValueStore) -> TokenBlocklist:
        """Provide the token blocklist.

        Args:
            store: Key-value store.

        Returns:
            TokenBlocklist: Configured blocklist.
        """
        return TokenBlocklist(store)

    @provide(scope=Scope.APP)
    async def csrf_service(self) -> CSRFService:
        """Provide the CSRF service.

        Returns:
            CSRFService: Configured service.
        """
        return CSRFService()

    @provide(scope=Scope.APP)
    async def account_lock_service(self, store: KeyValueStore) -> AccountLockService:
        """Provide the account lock service.

        Args:
            store: Key-value store.

        Returns:
            AccountLockService: Configured service.
        """
        return AccountLockService(store=store)

    @provide(scope=Scope.APP)
    async def rate_limiter(self, store: KeyValueStore) -> RateLimiter:
        """Provide the rate limiter.

        Args:
            store: Key-value store.

        Returns:
            RateLimiter: Configured limiter.
        """
        return RateLimiter(store)

    @provide(scope=Scope.APP)
    async def password_reset_mailer(self) -> PasswordResetMailer:
        """Provide the password reset mailer.

        Returns:
            PasswordResetMailer: Configured mailer.
        """
        return PasswordResetMailer()

    @provide(scope=Scope.APP)
    async def email_verification_mailer(self) -> EmailVerificationMailer:
        """Provide the email verification mailer.

        Returns:
            EmailVerificationMailer: Configured mailer.
        """
        return EmailVerificationMailer()

    @provide(scope=Scope.APP)
    async def telegram_support_notifier(self) -> AsyncIterator[TelegramSupportNotifier]:
        """Provide the Telegram support notifier.

        Yields:
            TelegramSupportNotifier: Configured notifier.
        """
        notifier = TelegramSupportNotifier()
        yield notifier
        await notifier.aclose()

    @provide(scope=Scope.APP)
    async def support_email_mailer(self) -> SupportEmailMailer:
        """Provide the support email mailer.

        Returns:
            SupportEmailMailer: Configured mailer.
        """
        return SupportEmailMailer()

    @provide(scope=Scope.APP)
    async def email_verification_store(self, store: KeyValueStore) -> EmailVerificationStore:
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
