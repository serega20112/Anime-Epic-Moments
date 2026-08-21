"""SQLAlchemy-модель лайка комментария обсуждения."""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)

from backend.infrastructure.files.database import Base


class AnimeDiscussionLikeModel(Base):
    """Таблица ``anime_discussion_likes``: лайк комментария обсуждения."""

    __tablename__ = "anime_discussion_likes"
    __table_args__ = (UniqueConstraint("comment_id", "user_id", name="uq_anime_discussion_like"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(
        Integer,
        ForeignKey("anime_discussion_comments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)
