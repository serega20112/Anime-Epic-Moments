from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain import (
    Highlight,
    HighlightActivityItem,
    HighlightCommentItem,
    HighlightEngagement,
    HighlightLikeUser,
    HighlightProfileSummary,
)
from backend.infrastructure.models import (
    HighlightCommentModel,
    HighlightContextModel,
    HighlightLikeModel,
    HighlightModel,
    SavedHighlightModel,
    UserModel,
)


class HighlightRepository:
    """Data access for highlights and their engagement."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, highlight: Highlight) -> Highlight:
        """Persist a new highlight.

        Args:
            highlight: Highlight aggregate to persist.

        Returns:
            Highlight: The persisted highlight.
        """
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
        return self._to_entity(db_highlight)

    async def get_by_id(self, highlight_id: int) -> Highlight | None:
        """Fetch a highlight by identifier.

        Args:
            highlight_id: Highlight identifier.

        Returns:
            Highlight | None: The highlight or None.
        """
        result = await self.session.execute(
            select(HighlightModel).where(HighlightModel.id == highlight_id)
        )
        row = result.scalar_one_or_none()
        return self._to_entity(row) if row else None

    async def update(self, highlight: Highlight) -> Highlight:
        """Update a highlight.

        Args:
            highlight: Highlight with updated fields.

        Returns:
            Highlight: The updated highlight.
        """
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
        return self._to_entity(db_highlight)

    async def delete(self, highlight_id: int):
        """Delete a highlight and its related rows.

        Args:
            highlight_id: Highlight identifier.
        """
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
        """Return highlights created by a user.

        Args:
            user_id: User identifier.

        Returns:
            list[Highlight]: User highlights.
        """
        result = await self.session.execute(
            select(HighlightModel).where(HighlightModel.user_id == user_id)
        )
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_by_users(self, user_ids: list[int], limit: int | None = None) -> list[Highlight]:
        """Return highlights created by the given users.

        Args:
            user_ids: User identifiers.
            limit: Maximum number of highlights.

        Returns:
            list[Highlight]: Matching highlights.
        """
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
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_public_top(self, limit: int = 20) -> list[Highlight]:
        """Return the most popular public highlights.

        Args:
            limit: Maximum number of highlights.

        Returns:
            list[Highlight]: Ranked highlights.
        """
        result = await self.session.execute(select(HighlightModel))
        return self._order_by_popularity(result.scalars().all(), limit=limit)

    async def get_public_recent(self, limit: int = 20) -> list[Highlight]:
        """Return the most recent highlights.

        Args:
            limit: Maximum number of highlights.

        Returns:
            list[Highlight]: Recent highlights.
        """
        result = await self.session.execute(
            select(HighlightModel).order_by(HighlightModel.created_at.desc()).limit(limit)
        )
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_by_anime_episode(
        self, anime_id: int, episode: int, user_id: int | None = None
    ) -> list[Highlight]:
        """Return highlights for an anime and episode.

        Args:
            anime_id: Anime identifier.
            episode: Episode number.
            user_id: Optional owning user to filter by.

        Returns:
            list[Highlight]: Matching highlights.
        """
        query = select(HighlightModel).where(
            HighlightModel.anime_id == anime_id,
            HighlightModel.episode == episode,
        )
        if user_id is not None:
            query = query.where(HighlightModel.user_id == user_id)
        result = await self.session.execute(query.order_by(HighlightModel.created_at.desc()))
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_saved_by_user(self, user_id: int, limit: int | None = None) -> list[Highlight]:
        """Return highlights saved by a user.

        Args:
            user_id: User identifier.
            limit: Maximum number of highlights.

        Returns:
            list[Highlight]: Saved highlights.
        """
        query = (
            select(HighlightModel)
            .join(SavedHighlightModel, SavedHighlightModel.highlight_id == HighlightModel.id)
            .where(SavedHighlightModel.user_id == user_id)
            .order_by(SavedHighlightModel.saved_at.desc())
        )
        if limit is not None:
            query = query.limit(limit)
        result = await self.session.execute(query)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_liked_by_user(self, user_id: int, limit: int | None = None) -> list[Highlight]:
        """Return highlights liked by a user.

        Args:
            user_id: User identifier.
            limit: Maximum number of highlights.

        Returns:
            list[Highlight]: Liked highlights.
        """
        query = (
            select(HighlightModel)
            .join(HighlightLikeModel, HighlightLikeModel.highlight_id == HighlightModel.id)
            .where(HighlightLikeModel.user_id == user_id)
            .order_by(HighlightLikeModel.created_at.desc())
        )
        if limit is not None:
            query = query.limit(limit)
        result = await self.session.execute(query)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_from_anime_ids(self, anime_ids: list[int], limit: int = 20) -> list[Highlight]:
        """Return popular highlights from the given anime.

        Args:
            anime_ids: Anime identifiers.
            limit: Maximum number of highlights.

        Returns:
            list[Highlight]: Ranked highlights.
        """
        if not anime_ids:
            return []
        result = await self.session.execute(
            select(HighlightModel).where(HighlightModel.anime_id.in_(anime_ids))
        )
        return self._order_by_popularity(result.scalars().all(), limit=limit)

    async def set_like(self, highlight_id: int, user_id: int, liked: bool) -> Highlight:
        """Set or remove a like on a highlight.

        Args:
            highlight_id: Highlight identifier.
            user_id: User identifier.
            liked: True to add a like, False to remove.

        Returns:
            Highlight: The updated highlight.
        """
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
            db_highlight.likes_count = int(db_highlight.likes_count or 0) + 1
        elif not liked and existing is not None:
            await self.session.delete(existing)
            db_highlight.likes_count = max(int(db_highlight.likes_count or 0) - 1, 0)
        await self.session.flush()
        return self._to_entity(db_highlight)

    async def get_likers(self, highlight_id: int, limit: int = 20) -> list[HighlightLikeUser]:
        """Return users who liked a highlight.

        Args:
            highlight_id: Highlight identifier.
            limit: Maximum number of likers.

        Returns:
            list[HighlightLikeUser]: Likers.
        """
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
        """Add a comment to a highlight.

        Args:
            highlight_id: Highlight identifier.
            user_id: Author user identifier.
            content: Comment text.

        Returns:
            HighlightCommentItem: The created comment.
        """
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
        """Return comments for a highlight.

        Args:
            highlight_id: Highlight identifier.
            limit: Maximum number of comments.

        Returns:
            list[HighlightCommentItem]: Comments.
        """
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
        """Save or unsave a highlight.

        Args:
            highlight_id: Highlight identifier.
            user_id: User identifier.
            saved: True to save, False to unsave.

        Returns:
            bool: True if the highlight is saved.
        """
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
        """Return engagement (comments, likes, saves) per highlight.

        Args:
            highlight_ids: Highlight identifiers.
            viewer_user_id: Optional viewer user.

        Returns:
            dict[int, HighlightEngagement]: Engagement map.
        """
        if not highlight_ids:
            return {}

        result = {highlight_id: HighlightEngagement() for highlight_id in highlight_ids}
        comment_result = await self.session.execute(
            select(
                HighlightCommentModel.highlight_id,
                func.count(HighlightCommentModel.id),
            )
            .where(HighlightCommentModel.highlight_id.in_(highlight_ids))
            .group_by(HighlightCommentModel.highlight_id)
        )
        for highlight_id, count in comment_result.all():
            result[int(highlight_id)].comments_count = int(count)

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
            for highlight_id in liked_result.scalars().all():
                result[int(highlight_id)].is_liked = True
            for highlight_id in saved_result.scalars().all():
                result[int(highlight_id)].is_saved = True

        return result

    async def increment_views(self, highlight_id: int) -> Highlight:
        """Increment the view count for a highlight.

        Args:
            highlight_id: Highlight identifier.

        Returns:
            Highlight: The updated highlight.
        """
        result = await self.session.execute(
            select(HighlightModel).where(HighlightModel.id == highlight_id)
        )
        db_highlight = result.scalar_one_or_none()
        if db_highlight is None:
            raise ValueError("Highlight не найден")
        db_highlight.views_count = int(db_highlight.views_count or 0) + 1
        await self.session.flush()

        return self._to_entity(db_highlight)

    async def get_profile_summary(self, user_id: int) -> HighlightProfileSummary:
        """Return highlight statistics for a user profile.

        Args:
            user_id: User identifier.

        Returns:
            HighlightProfileSummary: Highlight statistics.
        """
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
        """Return recent activity on the user's highlights.

        Args:
            user_id: User identifier.
            limit: Maximum number of activity items.

        Returns:
            list[HighlightActivityItem]: Recent activity.
        """
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

    async def _scalar_count(self, statement) -> int:
        """Execute a count statement and return the scalar value.

        Args:
            statement: SQLAlchemy count statement.

        Returns:
            int: The count value.
        """
        result = await self.session.execute(statement)
        return int(result.scalar() or 0)

    def _order_by_popularity(self, rows: Iterable[HighlightModel], limit: int) -> list[Highlight]:
        ranked = sorted(
            rows,
            key=lambda row: self._popularity_score(row),
            reverse=True,
        )
        return [self._to_entity(row) for row in ranked[:limit]]

    def _popularity_score(self, row: HighlightModel) -> float:
        age_hours = max(
            (datetime.utcnow() - (row.created_at or datetime.utcnow())).total_seconds() / 3600,
            0.0,
        )
        freshness_bonus = max(72.0 - age_hours, 0.0) / 12.0
        return (
            float(row.likes_count or 0) * 4.0 + float(row.views_count or 0) * 2.0 + freshness_bonus
        )

    def _to_entity(self, row: HighlightModel | None) -> Highlight:
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
