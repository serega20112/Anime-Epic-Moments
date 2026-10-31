"""Социальные действия: лайки, сохранения, комментарии и вовлечённость."""

from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain import (
    Highlight,
    HighlightCommentItem,
    HighlightEngagement,
    HighlightLikeUser,
)
from backend.infrastructure.database.models import (
    HighlightCommentModel,
    HighlightLikeModel,
    HighlightModel,
    SavedHighlightModel,
    UserModel,
)


class HighlightSocialMixin:
    """Социальные действия: лайки, сохранения, комментарии и вовлечённость.

    Атрибут `session` предоставляет composing-класс репозитория: все mixin'ы
    работают поверх одной сессии и одной транзакции.
    """

    session: AsyncSession

    async def set_like(self, highlight_id: int, user_id: int, liked: bool) -> Highlight:
        """Поставить или снять лайк хайлайту."""
        result = await self.session.execute(
            select(HighlightModel).where(HighlightModel.id == highlight_id)
        )
        db_highlight = result.scalar_one_or_none()
        if db_highlight is None:
            raise ValueError("Highlight не найден")

        like_result = await self.session.execute(
            select(HighlightLikeModel).where(
                HighlightLikeModel.highlight_id == highlight_id,
                HighlightLikeModel.user_id == user_id,
            )
        )
        existing = like_result.scalar_one_or_none()
        if liked and existing is None:
            self.session.add(HighlightLikeModel(highlight_id=highlight_id, user_id=user_id))
            await self.session.execute(
                update(HighlightModel)
                .where(HighlightModel.id == highlight_id)
                .values(likes_count=HighlightModel.likes_count + 1)
            )
        elif not liked and existing is not None:
            await self.session.delete(existing)
            await self.session.execute(
                update(HighlightModel)
                .where(
                    HighlightModel.id == highlight_id,
                    HighlightModel.likes_count > 0,
                )
                .values(likes_count=HighlightModel.likes_count - 1)
            )
        await self.session.flush()
        await self.session.refresh(db_highlight)
        return await self._to_entity(db_highlight)

    async def get_likers(self, highlight_id: int, limit: int = 20) -> list[HighlightLikeUser]:
        """Вернуть пользователей, поставивших лайк хайлайту."""
        result = await self.session.execute(
            select(HighlightLikeModel, UserModel.username)
            .join(UserModel, UserModel.id == HighlightLikeModel.user_id)
            .where(HighlightLikeModel.highlight_id == highlight_id)
            .order_by(HighlightLikeModel.created_at.desc())
            .limit(limit)
        )
        return [
            HighlightLikeUser(
                user_id=item.user_id,
                username=username,
                created_at=item.created_at.strftime("%Y-%m-%d %H:%M"),
            )
            for item, username in result.all()
        ]

    async def add_comment(
        self, highlight_id: int, user_id: int, content: str
    ) -> HighlightCommentItem:
        """Добавить комментарий к хайлайту."""
        result = await self.session.execute(
            select(HighlightModel).where(HighlightModel.id == highlight_id)
        )
        if result.scalar_one_or_none() is None:
            raise ValueError("Highlight не найден")

        db_comment = HighlightCommentModel(
            highlight_id=highlight_id,
            user_id=user_id,
            content=str(content or "").strip(),
        )
        self.session.add(db_comment)
        await self.session.flush()
        username_result = await self.session.execute(
            select(UserModel.username).where(UserModel.id == user_id)
        )
        username = username_result.scalar() or f"user-{user_id}"
        return HighlightCommentItem(
            id=db_comment.id,
            user_id=user_id,
            username=username,
            content=db_comment.content,
            created_at=db_comment.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    async def get_comments(self, highlight_id: int, limit: int = 20) -> list[HighlightCommentItem]:
        """Вернуть комментарии хайлайта."""
        result = await self.session.execute(
            select(HighlightCommentModel, UserModel.username)
            .join(UserModel, UserModel.id == HighlightCommentModel.user_id)
            .where(HighlightCommentModel.highlight_id == highlight_id)
            .order_by(HighlightCommentModel.created_at.desc())
            .limit(limit)
        )
        return [
            HighlightCommentItem(
                id=item.id,
                user_id=item.user_id,
                username=username,
                content=item.content,
                created_at=item.created_at.strftime("%Y-%m-%d %H:%M"),
            )
            for item, username in result.all()
        ]

    async def set_saved(self, highlight_id: int, user_id: int, saved: bool) -> bool:
        """Сохранить хайлайт или убрать его из сохранённых."""
        result = await self.session.execute(
            select(HighlightModel).where(HighlightModel.id == highlight_id)
        )
        if result.scalar_one_or_none() is None:
            raise ValueError("Highlight не найден")

        saved_result = await self.session.execute(
            select(SavedHighlightModel).where(
                SavedHighlightModel.highlight_id == highlight_id,
                SavedHighlightModel.user_id == user_id,
            )
        )
        existing = saved_result.scalar_one_or_none()
        if saved and existing is None:
            self.session.add(SavedHighlightModel(highlight_id=highlight_id, user_id=user_id))
            await self.session.flush()
            return True
        if not saved and existing is not None:
            await self.session.delete(existing)
            await self.session.flush()
            return False
        return bool(saved and existing is not None)

    async def get_engagement_map(
        self, highlight_ids: list[int], viewer_user_id: int | None = None
    ) -> dict[int, HighlightEngagement]:
        """Вернуть вовлечённость (комментарии, лайки, сохранения) по хайлайтам.

        Счётчики накапливаются в обычных словарях, а неизменяемые value objects
        собираются один раз в конце: реакция не должна переписываться после
        того, как ушла из репозитория в сценарий.
        """
        if not highlight_ids:
            return {}

        comments_by_id: dict[int, int] = {}
        liked_ids: set[int] = set()
        saved_ids: set[int] = set()

        comment_result = await self.session.execute(
            select(
                HighlightCommentModel.highlight_id,
                func.count(HighlightCommentModel.id),
            )
            .where(HighlightCommentModel.highlight_id.in_(highlight_ids))
            .group_by(HighlightCommentModel.highlight_id)
        )
        for highlight_id, count in comment_result.all():
            comments_by_id[int(highlight_id)] = int(count)

        if viewer_user_id is not None:
            liked_result = await self.session.execute(
                select(HighlightLikeModel.highlight_id).where(
                    HighlightLikeModel.user_id == viewer_user_id,
                    HighlightLikeModel.highlight_id.in_(highlight_ids),
                )
            )
            saved_result = await self.session.execute(
                select(SavedHighlightModel.highlight_id).where(
                    SavedHighlightModel.user_id == viewer_user_id,
                    SavedHighlightModel.highlight_id.in_(highlight_ids),
                )
            )
            liked_ids = {int(highlight_id) for highlight_id in liked_result.scalars().all()}
            saved_ids = {int(highlight_id) for highlight_id in saved_result.scalars().all()}

        return {
            highlight_id: HighlightEngagement(
                comments_count=comments_by_id.get(highlight_id, 0),
                is_liked=highlight_id in liked_ids,
                is_saved=highlight_id in saved_ids,
            )
            for highlight_id in highlight_ids
        }
