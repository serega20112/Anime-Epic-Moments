"""SQLAlchemy-модель оценки пользователя по аниме."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint

from backend.infrastructure.files.database import Base


class UserAnimeRatingModel(Base):
    """Таблица ``user_anime_ratings``: оценка пользователя по тайтлу."""

    __tablename__ = "user_anime_ratings"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "anime_id",
            name="uq_user_anime_ratings_user_anime",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    anime_id = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    rated_at = Column(DateTime, default=datetime.utcnow)
