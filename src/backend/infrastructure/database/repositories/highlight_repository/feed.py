"""Выборки лент и сводок: публичные топы, сохранённое, профиль, активность."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain import (
    Highlight,
    HighlightActivityItem,
    HighlightProfileSummary,
)
from backend.infrastructure.database.models import (
    HighlightCommentModel,
    HighlightLikeModel,
    HighlightModel,
    SavedHighlightModel,
    UserModel,
)


class HighlightFeedMixin:
    """Выборки лент и сводок: публичные топы, сохранённое, профиль, активность.

    Атрибут `session` предоставляет composing-класс репозитория: все mixin'ы
    работают поверх одной сессии и одной транзакции.
    """

    session: AsyncSession

    async def get_public_top(self, limit: int = 20) -> list[Highlight]:
        """Вернуть самые популярные публичные хайлайты."""
        result = await self.session.execute(select(HighlightModel))
        return await self._order_by_popularity(result.scalars().all(), limit=limit)

    async def get_public_recent(self, limit: int = 20) -> list[Highlight]:
        """Вернуть самые свежие хайлайты."""
        result = await self.session.execute(
            select(HighlightModel).order_by(HighlightModel.created_at.desc()).limit(limit)
        )
        return [await self._to_entity(row) for row in result.scalars().all()]

    async def get_saved_by_user(self, user_id: int, limit: int | None = None) -> list[Highlight]:
        """Вернуть хайлайты, сохранённые пользователем."""
        query = (
            select(HighlightModel)
            .join(SavedHighlightModel, SavedHighlightModel.highlight_id == HighlightModel.id)
            .where(SavedHighlightModel.user_id == user_id)
            .order_by(SavedHighlightModel.saved_at.desc())
        )
        if limit is not None:
            query = query.limit(limit)
        result = await self.session.execute(query)
        return [await self._to_entity(row) for row in result.scalars().all()]

    async def get_liked_by_user(self, user_id: int, limit: int | None = None) -> list[Highlight]:
        """Вернуть хайлайты, которым пользователь поставил лайк."""
        query = (
            select(HighlightModel)
            .join(HighlightLikeModel, HighlightLikeModel.highlight_id == HighlightModel.id)
            .where(HighlightLikeModel.user_id == user_id)
            .order_by(HighlightLikeModel.created_at.desc())
        )
        if limit is not None:
            query = query.limit(limit)
        result = await self.session.execute(query)
        return [await self._to_entity(row) for row in result.scalars().all()]

    async def get_profile_summary(self, user_id: int) -> HighlightProfileSummary:
        """Вернуть статистику хайлайтов для профиля."""
        highlight_count = await self._scalar_count(
            select(func.count(HighlightModel.id)).where(HighlightModel.user_id == user_id)
        )
        like_count = await self._scalar_count(
            select(func.count(HighlightLikeModel.id)).where(HighlightLikeModel.user_id == user_id)
        )
        saved_count = await self._scalar_count(
            select(func.count(SavedHighlightModel.id)).where(SavedHighlightModel.user_id == user_id)
        )
        return HighlightProfileSummary(
            highlight_count=int(highlight_count),
            like_count=int(like_count),
            saved_count=int(saved_count),
        )

    async def get_recent_activity(
        self, user_id: int, limit: int = 10
    ) -> list[HighlightActivityItem]:
        """Вернуть недавнюю активность по хайлайтам пользователя."""
        own_ids_result = await self.session.execute(
            select(HighlightModel.id).where(HighlightModel.user_id == user_id)
        )
        own_highlight_ids = [int(value) for value in own_ids_result.scalars().all()]
        if not own_highlight_ids:
            return []

        like_result = await self.session.execute(
            select(
                HighlightLikeModel,
                UserModel.username,
                HighlightModel.title,
            )
            .join(UserModel, UserModel.id == HighlightLikeModel.user_id)
            .join(HighlightModel, HighlightModel.id == HighlightLikeModel.highlight_id)
            .where(
                HighlightLikeModel.highlight_id.in_(own_highlight_ids),
                HighlightLikeModel.user_id != user_id,
            )
            .order_by(HighlightLikeModel.created_at.desc())
            .limit(limit)
        )
        comment_result = await self.session.execute(
            select(
                HighlightCommentModel,
                UserModel.username,
                HighlightModel.title,
            )
            .join(UserModel, UserModel.id == HighlightCommentModel.user_id)
            .join(HighlightModel, HighlightModel.id == HighlightCommentModel.highlight_id)
            .where(
                HighlightCommentModel.highlight_id.in_(own_highlight_ids),
                HighlightCommentModel.user_id != user_id,
            )
            .order_by(HighlightCommentModel.created_at.desc())
            .limit(limit)
        )

        items = [
            HighlightActivityItem(
                action="like",
                actor_user_id=item.user_id,
                actor_username=username,
                highlight_id=item.highlight_id,
                highlight_title=title or "Без названия",
                created_at=item.created_at.strftime("%Y-%m-%d %H:%M"),
            )
            for item, username, title in like_result.all()
        ]
        items.extend(
            HighlightActivityItem(
                action="comment",
                actor_user_id=item.user_id,
                actor_username=username,
                highlight_id=item.highlight_id,
                highlight_title=title or "Без названия",
                created_at=item.created_at.strftime("%Y-%m-%d %H:%M"),
            )
            for item, username, title in comment_result.all()
        )
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items[:limit]
