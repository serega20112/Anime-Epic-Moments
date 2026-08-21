"""SQLAlchemy-модель хайлайта."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)

from backend.infrastructure.files.database import Base


class HighlightModel(Base):
    """Таблица ``highlights``: момент серии, сохранённый пользователем."""

    __tablename__ = "highlights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    anime_id = Column(Integer, nullable=False)
    episode = Column(Integer, nullable=False)
    start_timestamp = Column(Float, nullable=False)
    end_timestamp = Column(Float, nullable=False)
    title = Column(String(120), nullable=False, default="")
    category = Column(String(40), nullable=True)
    description = Column(String, nullable=True)
    is_spoiler = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    likes_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)
    emotion = Column(String, nullable=True)
