from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.backend.domain.anime.value_object import AnimeDiscussionComment
from src.backend.domain.watch.entity import (
    HighlightContext,
    Translation,
    UserAnimeStatus,
    ViewingSession,
    WatchSource,
)
from src.backend.domain.watch.value_object import (
    ViewingHeatmapPoint,
    WatchedAnimeStat,
)
from src.backend.infrastructure.models.sqlalchemy_models import (
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
    def __init__(self, session: Session):
        self.session = session

    def get_status(self, user_id: int, anime_id: int) -> Optional[UserAnimeStatus]:
        row = (
            self.session.query(UserAnimeStatusModel)
            .filter_by(user_id=user_id, anime_id=anime_id)
            .first()
        )
        if not row:
            return None
        return UserAnimeStatus(
            id=row.id,
            user_id=row.user_id,
            anime_id=row.anime_id,
            status=row.status,
            updated_at=row.updated_at,
        )

    def upsert_status(self, status: UserAnimeStatus) -> UserAnimeStatus:
        row = (
            self.session.query(UserAnimeStatusModel)
            .filter_by(
                user_id=status.user_id,
                anime_id=status.anime_id,
            )
            .first()
        )
        if row:
            row.status = status.status
            row.updated_at = datetime.utcnow()
            self.session.commit()
            status.id = row.id
            status.updated_at = row.updated_at
            return status

        row = UserAnimeStatusModel(
            user_id=status.user_id,
            anime_id=status.anime_id,
            status=status.status,
        )
        self.session.add(row)
        self.session.commit()
        status.id = row.id
        status.updated_at = row.updated_at
        return status

    def get_translations(self, anime_id: int) -> List[Translation]:
        rows = (
            self.session.query(TranslationModel)
            .filter_by(anime_id=anime_id)
            .order_by(TranslationModel.name.asc())
            .all()
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
            for row in rows
        ]

    def add_translation(self, translation: Translation) -> Translation:
        existing = (
            self.session.query(TranslationModel)
            .filter_by(
                anime_id=translation.anime_id,
                name=translation.name,
                translation_type=translation.translation_type,
                language=translation.language,
            )
            .first()
        )
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
        self.session.commit()
        translation.id = row.id
        translation.created_at = row.created_at
        return translation

    def get_sources(
        self, anime_id: int, episode: int | None = None
    ) -> List[WatchSource]:
        query = self.session.query(WatchSourceModel).filter_by(anime_id=anime_id)
        if episode is not None:
            query = query.filter_by(episode=episode)
        rows = query.order_by(
            WatchSourceModel.episode.asc(), WatchSourceModel.quality_label.desc()
        ).all()
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
            for row in rows
        ]

    def add_source(self, source: WatchSource) -> WatchSource:
        existing = (
            self.session.query(WatchSourceModel)
            .filter_by(
                anime_id=source.anime_id,
                episode=source.episode,
                translation_id=source.translation_id,
                provider_name=source.provider_name,
                source_name=source.source_name,
                stream_url=source.stream_url,
                quality_label=source.quality_label,
                source_type=source.source_type,
            )
            .first()
        )
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
        self.session.commit()
        source.id = row.id
        source.created_at = row.created_at
        return source

    def get_session(
        self, user_id: int, anime_id: int, episode: int
    ) -> Optional[ViewingSession]:
        row = (
            self.session.query(ViewingSessionModel)
            .filter_by(
                user_id=user_id,
                anime_id=anime_id,
                episode=episode,
            )
            .first()
        )
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

    def upsert_session(self, session: ViewingSession) -> ViewingSession:
        row = (
            self.session.query(ViewingSessionModel)
            .filter_by(
                user_id=session.user_id,
                anime_id=session.anime_id,
                episode=session.episode,
            )
            .first()
        )
        if row:
            row.watch_source_id = session.watch_source_id
            row.position_seconds = session.position_seconds
            row.volume = session.volume
            row.quality_label = session.quality_label
            row.is_paused = session.is_paused
            row.updated_at = datetime.utcnow()
            self.session.commit()
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
        self.session.commit()
        session.id = row.id
        session.updated_at = row.updated_at
        return session

    def add_highlight_context(self, context: HighlightContext) -> HighlightContext:
        row = HighlightContextModel(
            highlight_id=context.highlight_id,
            watch_source_id=context.watch_source_id,
            translation_id=context.translation_id,
            title=context.title,
        )
        self.session.add(row)
        self.session.commit()
        context.id = row.id
        context.created_at = row.created_at
        return context

    def get_highlight_contexts(
        self, highlight_ids: List[int]
    ) -> List[HighlightContext]:
        if not highlight_ids:
            return []
        rows = (
            self.session.query(HighlightContextModel)
            .filter(HighlightContextModel.highlight_id.in_(highlight_ids))
            .all()
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
            for row in rows
        ]

    def get_watched_anime_stats(
        self,
        user_id: int,
        limit: int | None = None,
    ) -> List[WatchedAnimeStat]:
        query = (
            self.session.query(
                ViewingSessionModel.anime_id,
                func.sum(ViewingSessionModel.position_seconds).label("watched_seconds"),
                func.count(ViewingSessionModel.id).label("sessions_count"),
                func.max(ViewingSessionModel.updated_at).label("last_watched_at"),
            )
            .filter(ViewingSessionModel.user_id == user_id)
            .group_by(ViewingSessionModel.anime_id)
            .order_by(
                func.sum(ViewingSessionModel.position_seconds).desc(),
                func.max(ViewingSessionModel.updated_at).desc(),
            )
        )
        if limit is not None:
            query = query.limit(limit)
        rows = query.all()
        return [
            WatchedAnimeStat(
                anime_id=int(row.anime_id),
                watched_seconds=float(row.watched_seconds or 0.0),
                sessions_count=int(row.sessions_count or 0),
                last_watched_at=(
                    row.last_watched_at.strftime("%Y-%m-%d")
                    if row.last_watched_at
                    else ""
                ),
            )
            for row in rows
        ]

    def get_viewing_heatmap(
        self,
        user_id: int,
        days: int = 35,
    ) -> List[ViewingHeatmapPoint]:
        since = datetime.utcnow() - timedelta(days=max(int(days), 1) - 1)
        rows = (
            self.session.query(
                func.date(ViewingSessionModel.updated_at).label("activity_date"),
                func.count(ViewingSessionModel.id).label("interactions"),
            )
            .filter(
                ViewingSessionModel.user_id == user_id,
                ViewingSessionModel.updated_at >= since,
            )
            .group_by(func.date(ViewingSessionModel.updated_at))
            .order_by(func.date(ViewingSessionModel.updated_at).asc())
            .all()
        )
        return [
            ViewingHeatmapPoint(
                date=str(row.activity_date),
                interactions=int(row.interactions or 0),
            )
            for row in rows
        ]

    def add_anime_comment(
        self,
        anime_id: int,
        user_id: int,
        content: str,
    ) -> AnimeDiscussionComment:
        row = AnimeDiscussionCommentModel(
            anime_id=anime_id,
            user_id=user_id,
            content=str(content or "").strip(),
        )
        self.session.add(row)
        self.session.commit()
        username = (
            self.session.query(UserModel.username)
            .filter(UserModel.id == user_id)
            .scalar()
            or f"user-{user_id}"
        )
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

    def get_anime_comments(
        self,
        anime_id: int,
        sort_by: str = "popular",
        viewer_user_id: int | None = None,
        limit: int = 20,
    ) -> List[AnimeDiscussionComment]:
        rows = (
            self.session.query(
                AnimeDiscussionCommentModel,
                UserModel.username,
                func.count(AnimeDiscussionLikeModel.id).label("likes_count"),
            )
            .join(UserModel, UserModel.id == AnimeDiscussionCommentModel.user_id)
            .outerjoin(
                AnimeDiscussionLikeModel,
                AnimeDiscussionLikeModel.comment_id == AnimeDiscussionCommentModel.id,
            )
            .filter(AnimeDiscussionCommentModel.anime_id == anime_id)
            .group_by(AnimeDiscussionCommentModel.id, UserModel.username)
        )
        if str(sort_by).strip().lower() == "recent":
            rows = rows.order_by(AnimeDiscussionCommentModel.created_at.desc())
        else:
            rows = rows.order_by(
                func.count(AnimeDiscussionLikeModel.id).desc(),
                AnimeDiscussionCommentModel.created_at.desc(),
            )
        rows = rows.limit(limit).all()

        liked_ids: set[int] = set()
        if viewer_user_id is not None:
            liked_ids = {
                int(value)
                for (value,) in self.session.query(AnimeDiscussionLikeModel.comment_id)
                .join(
                    AnimeDiscussionCommentModel,
                    AnimeDiscussionCommentModel.id == AnimeDiscussionLikeModel.comment_id,
                )
                .filter(
                    AnimeDiscussionLikeModel.user_id == viewer_user_id,
                    AnimeDiscussionCommentModel.anime_id == anime_id,
                )
                .all()
            }
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

    def set_anime_comment_like(
        self,
        comment_id: int,
        user_id: int,
        liked: bool,
    ) -> AnimeDiscussionComment:
        comment = (
            self.session.query(AnimeDiscussionCommentModel)
            .filter_by(id=comment_id)
            .first()
        )
        if comment is None:
            raise ValueError("Комментарий не найден")
        existing = (
            self.session.query(AnimeDiscussionLikeModel)
            .filter_by(comment_id=comment_id, user_id=user_id)
            .first()
        )
        if liked and existing is None:
            self.session.add(
                AnimeDiscussionLikeModel(comment_id=comment_id, user_id=user_id)
            )
        elif not liked and existing is not None:
            self.session.delete(existing)
        self.session.commit()
        refreshed = self.get_anime_comments(
            anime_id=comment.anime_id,
            viewer_user_id=user_id,
            limit=200,
        )
        for item in refreshed:
            if item.id == comment_id:
                return item
        raise ValueError("Комментарий не найден")
