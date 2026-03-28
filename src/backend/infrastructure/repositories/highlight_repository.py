from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.backend.domain.highlight.entity import Highlight
from src.backend.domain.highlight.value_object import (
    HighlightActivityItem,
    HighlightCommentItem,
    HighlightEngagement,
    HighlightLikeUser,
    HighlightProfileSummary,
)
from src.backend.infrastructure.models.sqlalchemy_models import (
    HighlightCommentModel,
    HighlightContextModel,
    HighlightLikeModel,
    HighlightModel,
    SavedHighlightModel,
    UserModel,
)


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
            title=highlight.title,
            category=highlight.category,
            description=highlight.description,
            is_spoiler=highlight.is_spoiler,
            emotion=highlight.emotion,
            likes_count=highlight.likes_count,
            views_count=highlight.views_count,
        )
        self.session.add(db_highlight)
        self.session.commit()
        return self._to_entity(db_highlight)

    def get_by_id(self, highlight_id: int):
        row = self.session.query(HighlightModel).filter_by(id=highlight_id).first()
        return self._to_entity(row) if row else None

    def update(self, highlight: Highlight) -> Highlight:
        db_highlight = self.session.query(HighlightModel).filter_by(id=highlight.id).first()
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
        self.session.commit()
        return self._to_entity(db_highlight)

    def delete(self, highlight_id: int):
        self.session.query(HighlightLikeModel).filter_by(highlight_id=highlight_id).delete()
        self.session.query(HighlightCommentModel).filter_by(highlight_id=highlight_id).delete()
        self.session.query(SavedHighlightModel).filter_by(highlight_id=highlight_id).delete()
        self.session.query(HighlightContextModel).filter_by(highlight_id=highlight_id).delete()
        db_highlight = self.session.query(HighlightModel).filter_by(id=highlight_id).first()
        if db_highlight:
            self.session.delete(db_highlight)
            self.session.commit()

    def get_by_user(self, user_id: int) -> List[Highlight]:
        rows = self.session.query(HighlightModel).filter_by(user_id=user_id).all()
        return [self._to_entity(row) for row in rows]

    def get_public_top(self, limit: int = 20) -> List[Highlight]:
        rows = self.session.query(HighlightModel).all()
        return self._order_by_popularity(rows, limit=limit)

    def get_public_recent(self, limit: int = 20) -> List[Highlight]:
        rows = (
            self.session.query(HighlightModel)
            .order_by(HighlightModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [self._to_entity(row) for row in rows]

    def get_by_anime_episode(
        self, anime_id: int, episode: int, user_id: int | None = None
    ) -> List[Highlight]:
        query = self.session.query(HighlightModel).filter_by(
            anime_id=anime_id,
            episode=episode,
        )
        if user_id is not None:
            query = query.filter_by(user_id=user_id)
        rows = query.order_by(HighlightModel.created_at.desc()).all()
        return [self._to_entity(row) for row in rows]

    def get_saved_by_user(self, user_id: int, limit: int | None = None) -> List[Highlight]:
        query = (
            self.session.query(HighlightModel)
            .join(SavedHighlightModel, SavedHighlightModel.highlight_id == HighlightModel.id)
            .filter(SavedHighlightModel.user_id == user_id)
            .order_by(SavedHighlightModel.saved_at.desc())
        )
        if limit is not None:
            query = query.limit(limit)
        return [self._to_entity(row) for row in query.all()]

    def get_liked_by_user(self, user_id: int, limit: int | None = None) -> List[Highlight]:
        query = (
            self.session.query(HighlightModel)
            .join(HighlightLikeModel, HighlightLikeModel.highlight_id == HighlightModel.id)
            .filter(HighlightLikeModel.user_id == user_id)
            .order_by(HighlightLikeModel.created_at.desc())
        )
        if limit is not None:
            query = query.limit(limit)
        return [self._to_entity(row) for row in query.all()]

    def get_from_anime_ids(self, anime_ids: List[int], limit: int = 20) -> List[Highlight]:
        if not anime_ids:
            return []
        rows = (
            self.session.query(HighlightModel)
            .filter(HighlightModel.anime_id.in_(anime_ids))
            .all()
        )
        return self._order_by_popularity(rows, limit=limit)

    def set_like(self, highlight_id: int, user_id: int, liked: bool) -> Highlight:
        db_highlight = self.session.query(HighlightModel).filter_by(id=highlight_id).first()
        if db_highlight is None:
            raise ValueError("Highlight не найден")

        existing = (
            self.session.query(HighlightLikeModel)
            .filter_by(highlight_id=highlight_id, user_id=user_id)
            .first()
        )
        if liked and existing is None:
            self.session.add(HighlightLikeModel(highlight_id=highlight_id, user_id=user_id))
            db_highlight.likes_count = int(db_highlight.likes_count or 0) + 1
        elif not liked and existing is not None:
            self.session.delete(existing)
            db_highlight.likes_count = max(int(db_highlight.likes_count or 0) - 1, 0)
        self.session.commit()
        return self._to_entity(db_highlight)

    def get_likers(self, highlight_id: int, limit: int = 20) -> List[HighlightLikeUser]:
        rows = (
            self.session.query(HighlightLikeModel, UserModel.username)
            .join(UserModel, UserModel.id == HighlightLikeModel.user_id)
            .filter(HighlightLikeModel.highlight_id == highlight_id)
            .order_by(HighlightLikeModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            HighlightLikeUser(
                user_id=item.user_id,
                username=username,
                created_at=item.created_at.strftime("%Y-%m-%d %H:%M"),
            )
            for item, username in rows
        ]

    def add_comment(
        self, highlight_id: int, user_id: int, content: str
    ) -> HighlightCommentItem:
        db_highlight = self.session.query(HighlightModel).filter_by(id=highlight_id).first()
        if db_highlight is None:
            raise ValueError("Highlight не найден")

        db_comment = HighlightCommentModel(
            highlight_id=highlight_id,
            user_id=user_id,
            content=str(content or "").strip(),
        )
        self.session.add(db_comment)
        self.session.commit()
        username = (
            self.session.query(UserModel.username)
            .filter(UserModel.id == user_id)
            .scalar()
            or f"user-{user_id}"
        )
        return HighlightCommentItem(
            id=db_comment.id,
            user_id=user_id,
            username=username,
            content=db_comment.content,
            created_at=db_comment.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    def get_comments(
        self, highlight_id: int, limit: int = 20
    ) -> List[HighlightCommentItem]:
        rows = (
            self.session.query(HighlightCommentModel, UserModel.username)
            .join(UserModel, UserModel.id == HighlightCommentModel.user_id)
            .filter(HighlightCommentModel.highlight_id == highlight_id)
            .order_by(HighlightCommentModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            HighlightCommentItem(
                id=item.id,
                user_id=item.user_id,
                username=username,
                content=item.content,
                created_at=item.created_at.strftime("%Y-%m-%d %H:%M"),
            )
            for item, username in rows
        ]

    def set_saved(self, highlight_id: int, user_id: int, saved: bool) -> bool:
        db_highlight = self.session.query(HighlightModel).filter_by(id=highlight_id).first()
        if db_highlight is None:
            raise ValueError("Highlight не найден")

        existing = (
            self.session.query(SavedHighlightModel)
            .filter_by(highlight_id=highlight_id, user_id=user_id)
            .first()
        )
        if saved and existing is None:
            self.session.add(SavedHighlightModel(highlight_id=highlight_id, user_id=user_id))
            self.session.commit()
            return True
        if not saved and existing is not None:
            self.session.delete(existing)
            self.session.commit()
            return False
        return bool(saved and existing is not None)

    def get_engagement_map(
        self, highlight_ids: List[int], viewer_user_id: int | None = None
    ) -> dict[int, HighlightEngagement]:
        if not highlight_ids:
            return {}

        result = {highlight_id: HighlightEngagement() for highlight_id in highlight_ids}
        comment_rows = (
            self.session.query(
                HighlightCommentModel.highlight_id,
                func.count(HighlightCommentModel.id),
            )
            .filter(HighlightCommentModel.highlight_id.in_(highlight_ids))
            .group_by(HighlightCommentModel.highlight_id)
            .all()
        )
        for highlight_id, count in comment_rows:
            result[int(highlight_id)].comments_count = int(count)

        if viewer_user_id is not None:
            liked_ids = {
                int(value)
                for (value,) in self.session.query(HighlightLikeModel.highlight_id)
                .filter(
                    HighlightLikeModel.user_id == viewer_user_id,
                    HighlightLikeModel.highlight_id.in_(highlight_ids),
                )
                .all()
            }
            saved_ids = {
                int(value)
                for (value,) in self.session.query(SavedHighlightModel.highlight_id)
                .filter(
                    SavedHighlightModel.user_id == viewer_user_id,
                    SavedHighlightModel.highlight_id.in_(highlight_ids),
                )
                .all()
            }
            for highlight_id in liked_ids:
                result[highlight_id].is_liked = True
            for highlight_id in saved_ids:
                result[highlight_id].is_saved = True

        return result

    def increment_views(self, highlight_id: int) -> Highlight:
        db_highlight = self.session.query(HighlightModel).filter_by(id=highlight_id).first()
        if db_highlight is None:
            raise ValueError("Highlight не найден")
        db_highlight.views_count = int(db_highlight.views_count or 0) + 1
        self.session.commit()
        return self._to_entity(db_highlight)

    def get_profile_summary(self, user_id: int) -> HighlightProfileSummary:
        highlight_count = (
            self.session.query(func.count(HighlightModel.id))
            .filter(HighlightModel.user_id == user_id)
            .scalar()
            or 0
        )
        like_count = (
            self.session.query(func.count(HighlightLikeModel.id))
            .filter(HighlightLikeModel.user_id == user_id)
            .scalar()
            or 0
        )
        saved_count = (
            self.session.query(func.count(SavedHighlightModel.id))
            .filter(SavedHighlightModel.user_id == user_id)
            .scalar()
            or 0
        )
        return HighlightProfileSummary(
            highlight_count=int(highlight_count),
            like_count=int(like_count),
            saved_count=int(saved_count),
        )

    def get_recent_activity(
        self, user_id: int, limit: int = 10
    ) -> List[HighlightActivityItem]:
        own_highlight_ids = [
            int(value)
            for (value,) in self.session.query(HighlightModel.id)
            .filter(HighlightModel.user_id == user_id)
            .all()
        ]
        if not own_highlight_ids:
            return []

        like_rows = (
            self.session.query(
                HighlightLikeModel,
                UserModel.username,
                HighlightModel.title,
            )
            .join(UserModel, UserModel.id == HighlightLikeModel.user_id)
            .join(HighlightModel, HighlightModel.id == HighlightLikeModel.highlight_id)
            .filter(
                HighlightLikeModel.highlight_id.in_(own_highlight_ids),
                HighlightLikeModel.user_id != user_id,
            )
            .order_by(HighlightLikeModel.created_at.desc())
            .limit(limit)
            .all()
        )
        comment_rows = (
            self.session.query(
                HighlightCommentModel,
                UserModel.username,
                HighlightModel.title,
            )
            .join(UserModel, UserModel.id == HighlightCommentModel.user_id)
            .join(HighlightModel, HighlightModel.id == HighlightCommentModel.highlight_id)
            .filter(
                HighlightCommentModel.highlight_id.in_(own_highlight_ids),
                HighlightCommentModel.user_id != user_id,
            )
            .order_by(HighlightCommentModel.created_at.desc())
            .limit(limit)
            .all()
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
            for item, username, title in like_rows
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
            for item, username, title in comment_rows
        )
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items[:limit]

    def _order_by_popularity(self, rows: Iterable[HighlightModel], limit: int) -> List[Highlight]:
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
        return float(row.likes_count or 0) * 4.0 + float(row.views_count or 0) * 2.0 + freshness_bonus

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
