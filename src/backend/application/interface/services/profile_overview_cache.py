"""Порт кэша обзора профиля."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ProfileOverviewCacheInterface(ABC):
    """Кэш обзора профиля и ИИ-описания вкусов."""

    @abstractmethod
    async def get_overview(self, user_id: int) -> Any:
        """Прочитать обзор профиля из кэша."""

    @abstractmethod
    async def set_overview(self, user_id: int, overview: Any) -> Any:
        """Положить обзор профиля в кэш."""

    @abstractmethod
    async def get_ai_summary(self, user_id: int) -> str | None:
        """Прочитать ИИ-описание вкусов из кэша."""

    @abstractmethod
    async def set_ai_summary(self, user_id: int, summary: str) -> None:
        """Положить ИИ-описание вкусов в кэш."""

    @abstractmethod
    async def invalidate(self, user_id: int) -> None:
        """Сбросить закэшированные данные пользователя."""
