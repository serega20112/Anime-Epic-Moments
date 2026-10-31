"""Обсуждение аниме: комментарии и лайки комментариев.

Счётчик лайков не хранится в строке комментария, а считается агрегатом по таблице
`AnimeDiscussionLikeModel` — так исключается рассинхрон между счётчиком и фактом.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.value_objects.anime.discussion import AnimeDiscussionComment
from backend.infrastructure.database.models import (
    AnimeDiscussionCommentModel,
    AnimeDiscussionLikeModel,
    UserModel,
)


class AnimeDiscussionRepositoryMixin:
    """Доступ к комментариям обсуждения аниме и лайкам комментариев."""

    session: AsyncSession

    async def add_anime_comment(
        self,
        anime_id: int,
        user_id: int,
        content: str,
    ) -> AnimeDiscussionComment:
        """Создать комментарий обсуждения.

        Args:
            anime_id: Идентификатор аниме.
            user_id: Идентификатор автора.
            content: Текст комментария.

        Returns:
            AnimeDiscussionComment: Созданный комментарий.
        """
        row = AnimeDiscussionCommentModel(
            anime_id=anime_id,
            user_id=user_id,
            content=str(content or "").strip(),
        )
        self.session.add(row)
        await self.session.flush()
        username_result = await self.session.execute(
            select(UserModel.username).where(UserModel.id == user_id)
        )
        username = username_result.scalar() or f"user-{user_id}"
        return AnimeDiscussionComment(
            id=row.id,
            anime_id=row.anime_id,
            user_id=row.user_id,
            username=username,
            content=row.content,
            likes_count=0,
            created_at=row.created_at.strftime("%Y-%m-%d %H:%M"),
            is_liked=False,
        )

    async def get_anime_comments(
        self,
        anime_id: int,
        sort_by: str = "popular",
        viewer_user_id: int | None = None,
        limit: int = 20,
    ) -> list[AnimeDiscussionComment]:
        """Вернуть комментарии обсуждения аниме.

        Args:
            anime_id: Идентификатор аниме.
            sort_by: Режим сортировки: `popular` либо `recent`.
            viewer_user_id: Необязательный зритель — нужен для признаков лайка.
            limit: Максимальное число результатов.

        Returns:
            list[AnimeDiscussionComment]: Подходящие комментарии.
        """
        likes_count_expr = func.count(AnimeDiscussionLikeModel.id).label("likes_count")
        stmt = (
            select(AnimeDiscussionCommentModel, UserModel.username, likes_count_expr)
            .join(UserModel, UserModel.id == AnimeDiscussionCommentModel.user_id)
            .outerjoin(
                AnimeDiscussionLikeModel,
                AnimeDiscussionLikeModel.comment_id == AnimeDiscussionCommentModel.id,
            )
            .where(AnimeDiscussionCommentModel.anime_id == anime_id)
            .group_by(AnimeDiscussionCommentModel.id, UserModel.username)
        )
        if str(sort_by).strip().lower() == "recent":
            stmt = stmt.order_by(AnimeDiscussionCommentModel.created_at.desc())
        else:
            stmt = stmt.order_by(
                likes_count_expr.desc(),
                AnimeDiscussionCommentModel.created_at.desc(),
            )
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        rows = result.all()

        liked_ids: set[int] = set()
        if viewer_user_id is not None:
            liked_result = await self.session.execute(
                select(AnimeDiscussionLikeModel.comment_id)
                .join(
                    AnimeDiscussionCommentModel,
                    AnimeDiscussionCommentModel.id == AnimeDiscussionLikeModel.comment_id,
                )
                .where(
                    AnimeDiscussionLikeModel.user_id == viewer_user_id,
                    AnimeDiscussionCommentModel.anime_id == anime_id,
                )
            )
            liked_ids = {int(value) for (value,) in liked_result.all()}
        return [
            AnimeDiscussionComment(
                id=item.id,
                anime_id=item.anime_id,
                user_id=item.user_id,
                username=username,
                content=item.content,
                likes_count=int(likes_count or 0),
                created_at=item.created_at.strftime("%Y-%m-%d %H:%M"),
                is_liked=item.id in liked_ids,
            )
            for item, username, likes_count in rows
        ]

    async def set_anime_comment_like(
        self,
        comment_id: int,
        user_id: int,
        liked: bool,
    ) -> AnimeDiscussionComment:
        """Поставить или снять лайк с комментария.

        Args:
            comment_id: Идентификатор комментария.
            user_id: Идентификатор автора действия.
            liked: Лайк либо снятие лайка.

        Returns:
            AnimeDiscussionComment: Обновлённый комментарий.

        Raises:
            ValueError: Комментарий не найден.
        """
        result = await self.session.execute(
            select(AnimeDiscussionCommentModel).where(AnimeDiscussionCommentModel.id == comment_id)
        )
        comment = result.scalar_one_or_none()
        if comment is None:
            raise ValueError("Комментарий не найден")
        existing_result = await self.session.execute(
            select(AnimeDiscussionLikeModel).where(
                AnimeDiscussionLikeModel.comment_id == comment_id,
                AnimeDiscussionLikeModel.user_id == user_id,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if liked and existing is None:
            self.session.add(AnimeDiscussionLikeModel(comment_id=comment_id, user_id=user_id))
        elif not liked and existing is not None:
            await self.session.delete(existing)
        await self.session.flush()
        refreshed = await self.get_anime_comments(
            anime_id=comment.anime_id,
            viewer_user_id=user_id,
            limit=200,
        )
        for item in refreshed:
            if item.id == comment_id:
                return item
        raise ValueError("Комментарий не найден")
