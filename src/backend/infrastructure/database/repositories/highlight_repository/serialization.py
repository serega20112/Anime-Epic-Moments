"""Общие преобразования и счётные helper'ы репозитория хайлайтов."""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain import (
    Highlight,
)
from backend.domain.clock import utc_now
from backend.infrastructure.database.models import (
    HighlightModel,
)


class HighlightSerializationMixin:
    """Общие преобразования и счётные helper'ы репозитория хайлайтов.

    Атрибут `session` предоставляет composing-класс репозитория: все mixin'ы
    работают поверх одной сессии и одной транзакции.
    """

    session: AsyncSession

    async def _scalar_count(self, statement) -> int:
        """Выполнить запрос подсчёта и вернуть число."""
        result = await self.session.execute(statement)
        return int(result.scalar() or 0)

    async def _order_by_popularity(
        self, rows: Iterable[HighlightModel], limit: int
    ) -> list[Highlight]:
        """Упорядочить хайлайты по оценке популярности."""
        keyed = [(await self._popularity_score(row), row) for row in rows]
        keyed.sort(key=lambda pair: pair[0], reverse=True)
        ranked = [row for _score, row in keyed]
        return [await self._to_entity(row) for row in ranked[:limit]]

    async def _popularity_score(self, row: HighlightModel) -> float:
        """Посчитать оценку популярности хайлайта с бонусом за свежесть."""
        age_hours = max(
            (utc_now() - (row.created_at or utc_now())).total_seconds() / 3600,
            0.0,
        )
        freshness_bonus = max(72.0 - age_hours, 0.0) / 12.0
        return (
            float(row.likes_count or 0) * 4.0 + float(row.views_count or 0) * 2.0 + freshness_bonus
        )

    async def _to_entity(self, row: HighlightModel | None) -> Highlight:
        """Преобразовать строку базы в сущность хайлайта."""
        if row is None:
            raise ValueError("Highlight не найден")
        highlight = Highlight(
            user_id=row.user_id,
            anime_id=row.anime_id,
            episode=row.episode,
            start_timestamp=row.start_timestamp,
            end_timestamp=row.end_timestamp,
            title=row.title or "",
            category=row.category,
            description=row.description or "",
            is_spoiler=row.is_spoiler,
            emotion=row.emotion,
            created_at=row.created_at,
        )
        highlight.id = row.id
        highlight.likes_count = int(row.likes_count or 0)
        highlight.views_count = int(row.views_count or 0)
        return highlight
