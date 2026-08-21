"""SQLAlchemy-модель момента просмотра (черновик хайлайта)."""

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


class ViewingMomentModel(Base):
    """Таблица ``viewing_moments``: захват кадра во время просмотра до публикации."""

    __tablename__ = "viewing_moments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    anime_id = Column(Integer, nullable=False)
    episode = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False, default=0.0)
    watch_source_id = Column(
        Integer, ForeignKey("watch_sources.id", ondelete="SET NULL"), nullable=True
    )
    caption = Column(String(200), nullable=True)
    sticker = Column(String(40), nullable=True)
    screenshot_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
