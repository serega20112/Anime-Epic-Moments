"""Реализация репозитория: класс пакета и сборка mixin'ов по агрегатам."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from .crud import HighlightCrudMixin
from .feed import HighlightFeedMixin
from .serialization import HighlightSerializationMixin
from .social import HighlightSocialMixin

__all__ = [
    "HighlightCrudMixin",
    "HighlightFeedMixin",
    "HighlightRepository",
    "HighlightSerializationMixin",
    "HighlightSocialMixin",
]


class HighlightRepository(
    HighlightSerializationMixin,
    HighlightCrudMixin,
    HighlightFeedMixin,
    HighlightSocialMixin,
):
    """Доступ к данным хайлайтов и их социальных сущностей поверх одной сессии."""

    def __init__(self, session: AsyncSession):
        """Сохранить сессию, общую для всех mixin'ов репозитория.

        Args:
            session: Активная асинхронная сессия базы данных.
        """
        self.session = session
