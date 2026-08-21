"""SQLAlchemy-модель статуса просмотра тайтла пользователем."""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)

from backend.infrastructure.files.database import Base


class UserAnimeStatusModel(Base):
    """Таблица ``user_anime_statuses``: прогресс и оценка тайтла у пользователя."""

    __tablename__ = "user_anime_statuses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    anime_id = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    current_episode = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_watched_at = Column(DateTime, nullable=True)
    rating = Column(Float, nullable=True)
    note = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
