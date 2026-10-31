"""Порт кэша рекомендаций."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class RecommendationCacheInterface(ABC):
    """Кэш рекомендаций пользователя."""

    @abstractmethod
    async def get(self, user_id: int) -> Any:
        """Прочитать рекомендации из кэша."""

    @abstractmethod
    async def set(self, user_id: int, data: Any, ttl_seconds: int | None = None) -> None:
        """Положить рекомендации в кэш."""

    @abstractmethod
    async def invalidate(self, user_id: int) -> None:
        """Сбросить закэшированные рекомендации пользователя."""
