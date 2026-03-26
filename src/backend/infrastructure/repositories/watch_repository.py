from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from src.backend.domain.watch.entity import HighlightContext, Translation, UserAnimeStatus, ViewingSession, WatchSource
from src.backend.infrastructure.models.sqlalchemy_models import (
    HighlightContextModel,
    TranslationModel,
    UserAnimeStatusModel,
    ViewingSessionModel,
    WatchSourceModel,
)


class WatchRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_status(self, user_id: int, anime_id: int) -> Optional[UserAnimeStatus]:
        row = self.session.query(UserAnimeStatusModel).filter_by(user_id=user_id, anime_id=anime_id).first()
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
        row = self.session.query(UserAnimeStatusModel).filter_by(
            user_id=status.user_id,
            anime_id=status.anime_id,
        ).first()
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
        rows = self.session.query(TranslationModel).filter_by(anime_id=anime_id).order_by(TranslationModel.name.asc()).all()
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
        existing = self.session.query(TranslationModel).filter_by(
            anime_id=translation.anime_id,
            name=translation.name,
            translation_type=translation.translation_type,
            language=translation.language,
        ).first()
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

    def get_sources(self, anime_id: int, episode: int | None = None) -> List[WatchSource]:
        query = self.session.query(WatchSourceModel).filter_by(anime_id=anime_id)
        if episode is not None:
            query = query.filter_by(episode=episode)
        rows = query.order_by(WatchSourceModel.episode.asc(), WatchSourceModel.quality_label.desc()).all()
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
                created_at=row.created_at,
            )
            for row in rows
        ]

    def add_source(self, source: WatchSource) -> WatchSource:
        existing = self.session.query(WatchSourceModel).filter_by(
            anime_id=source.anime_id,
            episode=source.episode,
            translation_id=source.translation_id,
            provider_name=source.provider_name,
            source_name=source.source_name,
            stream_url=source.stream_url,
            quality_label=source.quality_label,
        ).first()
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
        )
        self.session.add(row)
        self.session.commit()
        source.id = row.id
        source.created_at = row.created_at
        return source

    def get_session(self, user_id: int, anime_id: int, episode: int) -> Optional[ViewingSession]:
        row = self.session.query(ViewingSessionModel).filter_by(
            user_id=user_id,
            anime_id=anime_id,
            episode=episode,
        ).first()
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
        row = self.session.query(ViewingSessionModel).filter_by(
            user_id=session.user_id,
            anime_id=session.anime_id,
            episode=session.episode,
        ).first()
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

    def get_highlight_contexts(self, highlight_ids: List[int]) -> List[HighlightContext]:
        if not highlight_ids:
            return []
        rows = self.session.query(HighlightContextModel).filter(HighlightContextModel.highlight_id.in_(highlight_ids)).all()
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
