"""Реализация репозитория: класс пакета и сборка mixin'ов по агрегатам."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from .analytics import WatchAnalyticsRepositoryMixin
from .discussion import AnimeDiscussionRepositoryMixin
from .progress import WatchProgressRepositoryMixin
from .sessions import ViewingSessionRepositoryMixin
from .sources import WatchSourceRepositoryMixin

__all__ = [
    "AnimeDiscussionRepositoryMixin",
    "ViewingSessionRepositoryMixin",
    "WatchAnalyticsRepositoryMixin",
    "WatchProgressRepositoryMixin",
    "WatchRepository",
    "WatchSourceRepositoryMixin",
]


class WatchRepository(
    WatchProgressRepositoryMixin,
    WatchSourceRepositoryMixin,
    ViewingSessionRepositoryMixin,
    WatchAnalyticsRepositoryMixin,
    AnimeDiscussionRepositoryMixin,
):
    """Доступ к данным зоны просмотра поверх одной сессии SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        """Сохранить сессию, общую для всех mixin'ов репозитория.

        Args:
            session: Активная асинхронная сессия базы данных.
        """
        self.session = session
