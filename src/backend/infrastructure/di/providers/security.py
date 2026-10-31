"""Безопасность: хеширование, JWT, blocklist, CSRF, блокировка аккаунта и rate limiting."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.interface.services import (
    CSRFServiceInterface,
    JWTServiceInterface,
    RateLimiterInterface,
    TokenBlocklistInterface,
)
from backend.config import Settings
from backend.infrastructure.cache.security_store import SecurityKeyValueStore
from backend.infrastructure.security.account_lock_service import AccountLockService
from backend.infrastructure.security.csrf_service import CSRFService
from backend.infrastructure.security.jwt_service import JWTService
from backend.infrastructure.security.password_service import PasswordService
from backend.infrastructure.security.rate_limiter import RateLimiter
from backend.infrastructure.security.token_blocklist import TokenBlocklist


class SecurityProvidersMixin(Provider):
    """Безопасность: хеширование, JWT, blocklist, CSRF, блокировка аккаунта и rate limiting.

    Часть провайдера: методы `@provide` собираются dishka из базовых
    классов, поэтому mixin самодостаточен и наследует `Provider`.
    """

    @provide(scope=Scope.APP)
    async def password_service(self) -> PasswordService:
        """Создать сервис хеширования паролей."""
        return PasswordService()

    @provide(scope=Scope.APP)
    async def jwt_service(self) -> JWTService:
        """Создать сервис JWT-токенов."""
        return JWTService()

    @provide(scope=Scope.APP)
    async def jwt_service_interface(self, service: JWTService) -> JWTServiceInterface:
        """Опубликовать сервис JWT через порт прикладного слоя.

        Args:
            service: Конкретный сервис JWT-токенов.

        Returns:
            JWTServiceInterface: Тот же сервис под абстракцией порта.
        """
        return service

    @provide(scope=Scope.APP)
    async def token_blocklist(self, store: SecurityKeyValueStore) -> TokenBlocklist:
        """Создать список отозванных токенов."""
        return TokenBlocklist(store)

    @provide(scope=Scope.APP)
    async def csrf_service(self) -> CSRFService:
        """Создать сервис CSRF-токенов."""
        return CSRFService()

    @provide(scope=Scope.APP)
    async def csrf_service_interface(self, service: CSRFService) -> CSRFServiceInterface:
        """Опубликовать сервис CSRF через порт прикладного слоя.

        Args:
            service: Конкретный сервис токенов CSRF.

        Returns:
            CSRFServiceInterface: Тот же сервис под абстракцией порта.
        """
        return service

    @provide(scope=Scope.APP)
    async def token_blocklist_interface(self, blocklist: TokenBlocklist) -> TokenBlocklistInterface:
        """Опубликовать список отозванных токенов через порт прикладного слоя.

        Args:
            blocklist: Конкретное хранилище отзыва.

        Returns:
            TokenBlocklistInterface: Тот же список под абстракцией порта.
        """
        return blocklist

    @provide(scope=Scope.APP)
    async def account_lock_service(self, store: SecurityKeyValueStore) -> AccountLockService:
        """Создать сервис блокировки аккаунта со сроком из конфигурации.

        Args:
            store: Хранилище счётчиков неудачных попыток и метки блокировки.

        Returns:
            AccountLockService: Сервис блокировки с настроенным сроком блокировки.
        """
        return AccountLockService(
            store=store,
            lock_duration_seconds=Settings.account_lock_duration_seconds,
        )

    @provide(scope=Scope.APP)
    async def rate_limiter(self, store: SecurityKeyValueStore) -> RateLimiter:
        """Создать ограничитель частоты запросов."""
        return RateLimiter(store)

    @provide(scope=Scope.APP)
    async def rate_limiter_interface(self, limiter: RateLimiter) -> RateLimiterInterface:
        """Опубликовать ограничитель частоты запросов через порт прикладного слоя.

        Args:
            limiter: Конкретный экземпляр счётчика.

        Returns:
            RateLimiterInterface: Тот же счётчик под абстракцией порта.
        """
        return limiter
