"""SQLAlchemy-модель сессии просмотра (состояние плеера)."""

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


class ViewingSessionModel(Base):
    """Таблица ``viewing_sessions``: позиция/громкость/качество для resume плеера."""

    __tablename__ = "viewing_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    anime_id = Column(Integer, nullable=False)
    episode = Column(Integer, nullable=False)
    watch_source_id = Column(
        Integer, ForeignKey("watch_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position_seconds = Column(Float, nullable=False, default=0.0)
    volume = Column(Float, nullable=False, default=1.0)
    quality_label = Column(String, nullable=False)
    is_paused = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow)
