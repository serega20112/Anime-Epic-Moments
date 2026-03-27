from sqlalchemy.orm import Session
from src.backend.infrastructure.models.sqlalchemy_models import HighlightModel
from src.backend.domain.highlight.entity import Highlight
from typing import List


class HighlightRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, highlight: Highlight) -> Highlight:
        db_highlight = HighlightModel(
            user_id=highlight.user_id,
            anime_id=highlight.anime_id,
            episode=highlight.episode,
            start_timestamp=highlight.start_timestamp,
            end_timestamp=highlight.end_timestamp,
            description=highlight.description,
            is_spoiler=highlight.is_spoiler,
            emotion=highlight.emotion,
        )
        self.session.add(db_highlight)
        self.session.commit()
        highlight.id = db_highlight.id
        highlight.created_at = db_highlight.created_at
        highlight.likes_count = db_highlight.likes_count
        return highlight

    def get_by_id(self, highlight_id: int):
        r = self.session.query(HighlightModel).filter_by(id=highlight_id).first()
        if not r:
            return None
        h = Highlight(
            user_id=r.user_id,
            anime_id=r.anime_id,
            episode=r.episode,
            start_timestamp=r.start_timestamp,
            end_timestamp=r.end_timestamp,
            description=r.description or "",
            is_spoiler=r.is_spoiler,
            emotion=r.emotion,
            created_at=r.created_at,
        )
        h.id = r.id
        h.likes_count = r.likes_count
        return h

    def update(self, highlight: Highlight) -> Highlight:
        db_highlight = (
            self.session.query(HighlightModel).filter_by(id=highlight.id).first()
        )
        if not db_highlight:
            raise ValueError("Highlight не найден")

        db_highlight.episode = highlight.episode
        db_highlight.start_timestamp = highlight.start_timestamp
        db_highlight.end_timestamp = highlight.end_timestamp
        db_highlight.description = highlight.description
        db_highlight.is_spoiler = highlight.is_spoiler
        db_highlight.emotion = highlight.emotion
        db_highlight.likes_count = highlight.likes_count
        self.session.commit()
        return highlight

    def delete(self, highlight_id: int):
        db_highlight = (
            self.session.query(HighlightModel).filter_by(id=highlight_id).first()
        )
        if db_highlight:
            self.session.delete(db_highlight)
            self.session.commit()

    def get_by_user(self, user_id: int) -> List[Highlight]:
        rows = self.session.query(HighlightModel).filter_by(user_id=user_id).all()
        result: List[Highlight] = []
        for r in rows:
            highlight = Highlight(
                user_id=r.user_id,
                anime_id=r.anime_id,
                episode=r.episode,
                start_timestamp=r.start_timestamp,
                end_timestamp=r.end_timestamp,
                description=r.description,
                is_spoiler=r.is_spoiler,
                emotion=r.emotion,
                created_at=r.created_at,
            )
            highlight.id = r.id
            highlight.likes_count = r.likes_count
            result.append(highlight)
        return result

    def get_public_top(self, limit: int = 20) -> List[Highlight]:
        rows = (
            self.session.query(HighlightModel)
            .order_by(HighlightModel.likes_count.desc())
            .limit(limit)
            .all()
        )

        result: List[Highlight] = []
        for r in rows:
            h = Highlight(
                user_id=r.user_id,
                anime_id=r.anime_id,
                episode=r.episode,
                start_timestamp=r.start_timestamp,
                end_timestamp=r.end_timestamp,
                description=r.description or "",
                is_spoiler=r.is_spoiler,
                emotion=r.emotion,
                created_at=r.created_at,
            )
            h.id = r.id
            h.likes_count = r.likes_count
            result.append(h)

        return result

    def get_by_anime_episode(
        self, anime_id: int, episode: int, user_id: int | None = None
    ) -> List[Highlight]:
        query = self.session.query(HighlightModel).filter_by(
            anime_id=anime_id, episode=episode
        )
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        rows = query.order_by(HighlightModel.created_at.desc()).all()

        result: List[Highlight] = []
        for r in rows:
            h = Highlight(
                user_id=r.user_id,
                anime_id=r.anime_id,
                episode=r.episode,
                start_timestamp=r.start_timestamp,
                end_timestamp=r.end_timestamp,
                description=r.description or "",
                is_spoiler=r.is_spoiler,
                emotion=r.emotion,
                created_at=r.created_at,
            )
            h.id = r.id
            h.likes_count = r.likes_count
            result.append(h)
        return result
