from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain import (
    HighlightContext,
    Translation,
    UserAnimeStatus,
    ViewingSession,
    WatchSource,
)
from backend.domain.anime.value_object import AnimeDiscussionComment
from backend.domain.watch.value_object import (
    ViewingHeatmapPoint,
    WatchedAnimeStat,
)
from backend.infrastructure.models import (
    AnimeDiscussionCommentModel,
    AnimeDiscussionLikeModel,
    HighlightContextModel,
    TranslationModel,
    UserAnimeStatusModel,
    UserModel,
    ViewingSessionModel,
    WatchSourceModel,
)


class WatchRepository:
    """Data access for watch-related domain objects."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_status(self, user_id: int, anime_id: int) -> UserAnimeStatus | None:
        """Fetch the anime status of a user.

        Args:
            user_id: User identifier.
            anime_id: Anime identifier.

        Returns:
            UserAnimeStatus | None: The status or None when missing.
        """
        result = await self.session.execute(
            select(UserAnimeStatusModel).where(
                UserAnimeStatusModel.user_id == user_id,
                UserAnimeStatusModel.anime_id == anime_id,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return UserAnimeStatus(
            id=row.id,
            user_id=row.user_id,
            anime_id=row.anime_id,
            status=row.status,
            updated_at=row.updated_at,
        )

    async def upsert_status(self, status: UserAnimeStatus) -> UserAnimeStatus:
        """Create or update an anime status.

        Args:
            status: Status aggregate to persist.

        Returns:
            UserAnimeStatus: The persisted status.
        """
        result = await self.session.execute(
            select(UserAnimeStatusModel).where(
                UserAnimeStatusModel.user_id == status.user_id,
                UserAnimeStatusModel.anime_id == status.anime_id,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            row.status = status.status
            row.updated_at = datetime.utcnow()
            await self.session.flush()
            status.id = row.id
            status.updated_at = row.updated_at
            return status

        row = UserAnimeStatusModel(
            user_id=status.user_id,
            anime_id=status.anime_id,
            status=status.status,
        )
        self.session.add(row)
        await self.session.flush()
        status.id = row.id
        status.updated_at = row.updated_at
        return status

    async def get_translations(self, anime_id: int) -> list[Translation]:
        """Fetch translations for an anime.

        Args:
            anime_id: Anime identifier.

        Returns:
            list[Translation]: Matching translations.
        """
        result = await self.session.execute(
            select(TranslationModel)
            .where(TranslationModel.anime_id == anime_id)
            .order_by(TranslationModel.name.asc())
        )
        return [
            Translation(
                id=row.id,
                anime_id=row.anime_id,
                name=row.name,
                translation_type=row.translation_type,
                language=row.language,
                created_at=row.created_at,
            )
            for row in result.scalars().all()
        ]

    async def add_translation(self, translation: Translation) -> Translation:
        """Create a translation unless an identical one already exists.

        Args:
            translation: Translation aggregate to persist.

        Returns:
            Translation: The existing or newly created translation.
        """
        result = await self.session.execute(
            select(TranslationModel).where(
                TranslationModel.anime_id == translation.anime_id,
                TranslationModel.name == translation.name,
                TranslationModel.translation_type == translation.translation_type,
                TranslationModel.language == translation.language,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            translation.id = existing.id
            translation.created_at = existing.created_at
            return translation

        row = TranslationModel(
            anime_id=translation.anime_id,
            name=translation.name,
            translation_type=translation.translation_type,
            language=translation.language,
        )
        self.session.add(row)
        await self.session.flush()
        translation.id = row.id
        translation.created_at = row.created_at
        return translation

    async def get_sources(
        self,
        anime_id: int,
        episode: int | None = None,
    ) -> list[WatchSource]:
        """Fetch watch sources for an anime.

        Args:
            anime_id: Anime identifier.
            episode: Optional episode filter.

        Returns:
            list[WatchSource]: Matching watch sources.
        """
        stmt = select(WatchSourceModel).where(WatchSourceModel.anime_id == anime_id)
        if episode is not None:
            stmt = stmt.where(WatchSourceModel.episode == episode)
        stmt = stmt.order_by(WatchSourceModel.episode.asc(), WatchSourceModel.quality_label.desc())
        result = await self.session.execute(stmt)
        return [
            WatchSource(
                id=row.id,
                anime_id=row.anime_id,
                episode=row.episode,
                translation_id=row.translation_id,
                provider_name=row.provider_name,
                source_name=row.source_name,
                stream_url=row.stream_url,
                quality_label=row.quality_label,
                source_type=row.source_type or "stream",
                created_at=row.created_at,
            )
            for row in result.scalars().all()
        ]

    async def add_source(self, source: WatchSource) -> WatchSource:
        """Create a watch source unless an identical one already exists.

        Args:
            source: Watch source aggregate to persist.

        Returns:
            WatchSource: The existing or newly created watch source.
        """
        result = await self.session.execute(
            select(WatchSourceModel).where(
                WatchSourceModel.anime_id == source.anime_id,
                WatchSourceModel.episode == source.episode,
                WatchSourceModel.translation_id == source.translation_id,
                WatchSourceModel.provider_name == source.provider_name,
                WatchSourceModel.source_name == source.source_name,
                WatchSourceModel.stream_url == source.stream_url,
                WatchSourceModel.quality_label == source.quality_label,
                WatchSourceModel.source_type == source.source_type,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            source.id = existing.id
            source.created_at = existing.created_at
            return source

        row = WatchSourceModel(
            anime_id=source.anime_id,
            episode=source.episode,
            translation_id=source.translation_id,
            provider_name=source.provider_name,
            source_name=source.source_name,
            stream_url=source.stream_url,
            quality_label=source.quality_label,
            source_type=source.source_type,
        )
        self.session.add(row)
        await self.session.flush()
        source.id = row.id
        source.created_at = row.created_at
        return source

    async def get_session(
        self,
        user_id: int,
        anime_id: int,
        episode: int,
    ) -> ViewingSession | None:
        """Fetch a viewing session for a user and episode.

        Args:
            user_id: User identifier.
            anime_id: Anime identifier.
            episode: Episode number.

        Returns:
            ViewingSession | None: The session or None when missing.
        """
        result = await self.session.execute(
            select(ViewingSessionModel).where(
                ViewingSessionModel.user_id == user_id,
                ViewingSessionModel.anime_id == anime_id,
                ViewingSessionModel.episode == episode,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return ViewingSession(
            id=row.id,
            user_id=row.user_id,
            anime_id=row.anime_id,
            episode=row.episode,
            watch_source_id=row.watch_source_id,
            position_seconds=row.position_seconds,
            volume=row.volume,
            quality_label=row.quality_label,
            is_paused=row.is_paused,
            updated_at=row.updated_at,
        )

    async def upsert_session(self, session: ViewingSession) -> ViewingSession:
        """Create or update a viewing session.

        Args:
            session: Viewing session aggregate to persist.

        Returns:
            ViewingSession: The persisted session.
        """
        result = await self.session.execute(
            select(ViewingSessionModel).where(
                ViewingSessionModel.user_id == session.user_id,
                ViewingSessionModel.anime_id == session.anime_id,
                ViewingSessionModel.episode == session.episode,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            row.watch_source_id = session.watch_source_id
            row.position_seconds = session.position_seconds
            row.volume = session.volume
            row.quality_label = session.quality_label
            row.is_paused = session.is_paused
            row.updated_at = datetime.utcnow()
            await self.session.flush()
            session.id = row.id
            session.updated_at = row.updated_at
            return session

        row = ViewingSessionModel(
            user_id=session.user_id,
            anime_id=session.anime_id,
            episode=session.episode,
            watch_source_id=session.watch_source_id,
            position_seconds=session.position_seconds,
            volume=session.volume,
            quality_label=session.quality_label,
            is_paused=session.is_paused,
        )
        self.session.add(row)
        await self.session.flush()
        session.id = row.id
        session.updated_at = row.updated_at
        return session

    async def add_highlight_context(self, context: HighlightContext) -> HighlightContext:
        """Create a highlight context.

        Args:
            context: Highlight context aggregate to persist.

        Returns:
            HighlightContext: The persisted context.
        """
        row = HighlightContextModel(
            highlight_id=context.highlight_id,
            watch_source_id=context.watch_source_id,
            translation_id=context.translation_id,
            title=context.title,
        )
        self.session.add(row)
        await self.session.flush()
        context.id = row.id
        context.created_at = row.created_at
        return context

    async def get_highlight_contexts(self, highlight_ids: list[int]) -> list[HighlightContext]:
        """Fetch highlight contexts by highlight identifiers.

        Args:
            highlight_ids: Highlight identifiers.

        Returns:
            list[HighlightContext]: Matching contexts.
        """
        if not highlight_ids:
            return []
        result = await self.session.execute(
            select(HighlightContextModel).where(
                HighlightContextModel.highlight_id.in_(highlight_ids)
            )
        )
        return [
            HighlightContext(
                id=row.id,
                highlight_id=row.highlight_id,
                watch_source_id=row.watch_source_id,
                translation_id=row.translation_id,
                title=row.title,
                created_at=row.created_at,
            )
            for row in result.scalars().all()
        ]

    async def get_watched_anime_stats(
        self,
        user_id: int,
        limit: int | None = None,
    ) -> list[WatchedAnimeStat]:
        """Compute watch statistics per anime for a user.

        Args:
            user_id: User identifier.
            limit: Maximum number of results.

        Returns:
            list[WatchedAnimeStat]: Per-anime watch statistics.
        """
        watched_seconds_expr = func.sum(ViewingSessionModel.position_seconds).label(
            "watched_seconds"
        )
        stmt = (
            select(
                ViewingSessionModel.anime_id,
                watched_seconds_expr,
                func.count(ViewingSessionModel.id).label("sessions_count"),
                func.max(ViewingSessionModel.updated_at).label("last_watched_at"),
            )
            .where(ViewingSessionModel.user_id == user_id)
            .group_by(ViewingSessionModel.anime_id)
            .order_by(
                watched_seconds_expr.desc(),
                func.max(ViewingSessionModel.updated_at).desc(),
            )
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            WatchedAnimeStat(
                anime_id=int(row.anime_id),
                watched_seconds=float(row.watched_seconds or 0.0),
                sessions_count=int(row.sessions_count or 0),
                last_watched_at=(
                    row.last_watched_at.strftime("%Y-%m-%d") if row.last_watched_at else ""
                ),
            )
            for row in rows
        ]

    async def get_viewing_heatmap(
        self,
        user_id: int,
        days: int = 35,
    ) -> list[ViewingHeatmapPoint]:
        """Compute daily viewing activity for a user.

        Args:
            user_id: User identifier.
            days: Number of days to include.

        Returns:
            list[ViewingHeatmapPoint]: Daily activity points.
        """
        since = datetime.utcnow() - timedelta(days=max(int(days), 1) - 1)
        activity_date_expr = func.date(ViewingSessionModel.updated_at).label("activity_date")
        stmt = (
            select(
                activity_date_expr,
                func.count(ViewingSessionModel.id).label("interactions"),
            )
            .where(
                ViewingSessionModel.user_id == user_id,
                ViewingSessionModel.updated_at >= since,
            )
            .group_by(activity_date_expr)
            .order_by(activity_date_expr.asc())
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        return [
            ViewingHeatmapPoint(
                date=str(row.activity_date),
                interactions=int(row.interactions or 0),
            )
            for row in rows
        ]

    async def add_anime_comment(
        self,
        anime_id: int,
        user_id: int,
        content: str,
    ) -> AnimeDiscussionComment:
        """Create an anime discussion comment.

        Args:
            anime_id: Anime identifier.
            user_id: Author identifier.
            content: Comment text.

        Returns:
            AnimeDiscussionComment: The created comment.
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
        """Fetch anime discussion comments.

        Args:
            anime_id: Anime identifier.
            sort_by: Sorting mode, either popular or recent.
            viewer_user_id: Optional viewer for like flags.
            limit: Maximum number of results.

        Returns:
            list[AnimeDiscussionComment]: Matching comments.
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
        """Set or unset a like on an anime discussion comment.

        Args:
            comment_id: Comment identifier.
            user_id: Actor identifier.
            liked: Whether to like or unlike the comment.

        Returns:
            AnimeDiscussionComment: The updated comment.

        Raises:
            ValueError: When the comment does not exist.
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
        refreshed = await self._get_anime_comments(
            anime_id=comment.anime_id,
            viewer_user_id=user_id,
            limit=200,
        )
        for item in refreshed:
            if item.id == comment_id:
                return item
        raise ValueError("Комментарий не найден")
