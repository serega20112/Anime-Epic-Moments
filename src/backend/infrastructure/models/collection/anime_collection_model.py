"""SQLAlchemy-модель коллекции аниме."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)

from backend.infrastructure.files.database import Base


class AnimeCollectionModel(Base):
    """Таблица ``anime_collections``: пользовательская подборка тайтлов."""

    __tablename__ = "anime_collections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = Column(String(80), nullable=False)
    description = Column(String(400), nullable=True)
    is_public = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
