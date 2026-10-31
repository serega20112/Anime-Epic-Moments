"""Создание, чтение, изменение и удаление самих хайлайтов."""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain import (
    Highlight,
)
from backend.infrastructure.database.models import (
    HighlightCommentModel,
    HighlightContextModel,
    HighlightLikeModel,
    HighlightModel,
    SavedHighlightModel,
)


class HighlightCrudMixin:
    """Создание, чтение, изменение и удаление самих хайлайтов.

    Атрибут `session` предоставляет composing-класс репозитория: все mixin'ы
    работают поверх одной сессии и одной транзакции.
    """

    session: AsyncSession

    async def add(self, highlight: Highlight) -> Highlight:
        """Сохранить новый хайлайт."""
        db_highlight = HighlightModel(
            user_id=highlight.user_id,
            anime_id=highlight.anime_id,
            episode=highlight.episode,
            start_timestamp=highlight.start_timestamp,
            end_timestamp=highlight.end_timestamp,
            title=highlight.title,
            category=highlight.category,
            description=highlight.description,
            is_spoiler=highlight.is_spoiler,
            emotion=highlight.emotion,
            likes_count=highlight.likes_count,
            views_count=highlight.views_count,
        )
        self.session.add(db_highlight)
        await self.session.flush()
        return await self._to_entity(db_highlight)

    async def get_by_id(self, highlight_id: int) -> Highlight | None:
        """Загрузить хайлайт по идентификатору."""
        result = await self.session.execute(
            select(HighlightModel).where(HighlightModel.id == highlight_id)
        )
        row = result.scalar_one_or_none()
        return await self._to_entity(row) if row else None

    async def update(self, highlight: Highlight) -> Highlight:
        """Обновить хайлайт."""
        result = await self.session.execute(
            select(HighlightModel).where(HighlightModel.id == highlight.id)
        )
        db_highlight = result.scalar_one_or_none()
        if not db_highlight:
            raise ValueError("Highlight не найден")

        db_highlight.episode = highlight.episode
        db_highlight.start_timestamp = highlight.start_timestamp
        db_highlight.end_timestamp = highlight.end_timestamp
        db_highlight.title = highlight.title
        db_highlight.category = highlight.category
        db_highlight.description = highlight.description
        db_highlight.is_spoiler = highlight.is_spoiler
        db_highlight.emotion = highlight.emotion
        db_highlight.likes_count = highlight.likes_count
        db_highlight.views_count = highlight.views_count
        await self.session.flush()
        return await self._to_entity(db_highlight)

    async def delete(self, highlight_id: int):
        """Удалить хайлайт вместе со связанными записями."""
        await self.session.execute(
            select(HighlightLikeModel).where(HighlightLikeModel.highlight_id == highlight_id)
        )
        await self.session.execute(
            select(HighlightCommentModel).where(HighlightCommentModel.highlight_id == highlight_id)
        )
        await self.session.execute(
            select(SavedHighlightModel).where(SavedHighlightModel.highlight_id == highlight_id)
        )
        await self.session.execute(
            select(HighlightContextModel).where(HighlightContextModel.highlight_id == highlight_id)
        )
        result = await self.session.execute(
            select(HighlightModel).where(HighlightModel.id == highlight_id)
        )
        db_highlight = result.scalar_one_or_none()
        if db_highlight:
            await self.session.delete(db_highlight)
            await self.session.flush()

    async def get_by_user(self, user_id: int) -> list[Highlight]:
        """Вернуть хайлайты, созданные пользователем."""
        result = await self.session.execute(
            select(HighlightModel).where(HighlightModel.user_id == user_id)
        )
        return [await self._to_entity(row) for row in result.scalars().all()]

    async def get_by_users(self, user_ids: list[int], limit: int | None = None) -> list[Highlight]:
        """Вернуть хайлайты указанных пользователей."""
        if not user_ids:
            return []
        query = (
            select(HighlightModel)
            .where(HighlightModel.user_id.in_(user_ids))
            .order_by(HighlightModel.created_at.desc())
        )
        if limit is not None:
            query = query.limit(limit)
        result = await self.session.execute(query)
        return [await self._to_entity(row) for row in result.scalars().all()]

    async def get_by_anime_episode(
        self, anime_id: int, episode: int, user_id: int | None = None
    ) -> list[Highlight]:
        """Вернуть хайлайты по аниме и серии."""
        query = select(HighlightModel).where(
            HighlightModel.anime_id == anime_id,
            HighlightModel.episode == episode,
        )
        if user_id is not None:
            query = query.where(HighlightModel.user_id == user_id)
        result = await self.session.execute(query.order_by(HighlightModel.created_at.desc()))
        return [await self._to_entity(row) for row in result.scalars().all()]

    async def get_from_anime_ids(self, anime_ids: list[int], limit: int = 20) -> list[Highlight]:
        """Вернуть популярные хайлайты указанных аниме."""
        if not anime_ids:
            return []
        result = await self.session.execute(
            select(HighlightModel).where(HighlightModel.anime_id.in_(anime_ids))
        )
        return await self._order_by_popularity(result.scalars().all(), limit=limit)

    async def increment_views(self, highlight_id: int) -> Highlight:
        """Увеличить счётчик просмотров хайлайта."""
        result = await self.session.execute(
            select(HighlightModel).where(HighlightModel.id == highlight_id)
        )
        db_highlight = result.scalar_one_or_none()
        if db_highlight is None:
            raise ValueError("Highlight не найден")
        await self.session.execute(
            update(HighlightModel)
            .where(HighlightModel.id == highlight_id)
            .values(views_count=HighlightModel.views_count + 1)
        )
        await self.session.flush()
        await self.session.refresh(db_highlight)

        return await self._to_entity(db_highlight)
