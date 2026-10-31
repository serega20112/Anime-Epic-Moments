"""Оконный счётчик запросов поверх общего хранилища ключ-значение."""

from __future__ import annotations

from backend.application.interface.services.rate_limiter import (
    RateLimitDecision,
    RateLimiterInterface,
)
from backend.infrastructure.cache.key_value_store import KeyValueStore

__all__ = ["RateLimitDecision", "RateLimiter"]


class RateLimiter(RateLimiterInterface):
    """Увеличивает и проверяет оконные счётчики запросов."""

    def __init__(self, store: KeyValueStore) -> None:
        """Инициализирует счётчик поверх хранилища ключ-значение.

        Args:
            store: Хранилище, в котором живёт счётчик окна.
        """
        self.store = store

    @staticmethod
    def build_key(scope: str, subject: str) -> str:
        """Собирает ключ счётчика по области и субъекту.

        Args:
            scope: Область ограничения.
            subject: Субъект ограничения, обычно IP или идентификатор.

        Returns:
            str: Нормализованный ключ счётчика.
        """
        normalized_scope = str(scope or "default").strip().lower()
        normalized_subject = str(subject or "anonymous").strip().lower()
        return f"rate_limit:{normalized_scope}:{normalized_subject}"

    async def hit(
        self,
        scope: str,
        subject: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        """Учитывает запрос и проверяет, не исчерпан ли лимит.

        Args:
            scope: Область ограничения.
            subject: Субъект ограничения.
            limit: Максимум запросов в окне.
            window_seconds: Размер окна в секундах.

        Returns:
            RateLimitDecision: Решение по текущему запросу.
        """
        key = self.build_key(scope, subject)
        current_count = await self.store.increment(
            key,
            ttl_seconds=max(int(window_seconds), 1),
            amount=1,
        )
        retry_after = await self.store.get_ttl(key)
        allowed = current_count <= int(limit)
        return RateLimitDecision(
            allowed=allowed,
            current_count=current_count,
            remaining=max(int(limit) - current_count, 0),
            retry_after=max(int(retry_after), 0),
        )

    async def current(self, scope: str, subject: str) -> int:
        """Читает текущее значение счётчика без его увеличения.

        Args:
            scope: Область ограничения.
            subject: Субъект ограничения.

        Returns:
            int: Число запросов, учтённых в текущем окне.
        """
        value = await self.store.get(self.build_key(scope, subject))
        try:
            return max(int(value or 0), 0)
        except (TypeError, ValueError):
            return 0
