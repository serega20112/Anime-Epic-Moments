"""SQLAlchemy-модель комментария обсуждения аниме."""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)

from backend.infrastructure.files.database import Base


class AnimeDiscussionCommentModel(Base):
    """Таблица ``anime_discussion_comments``: комментарий в обсуждении тайтла."""

    __tablename__ = "anime_discussion_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    anime_id = Column(Integer, nullable=False)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content = Column(String(600), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
