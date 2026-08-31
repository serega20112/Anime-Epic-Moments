"""SQLAlchemy-модель избранного аниме."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from backend.infrastructure.files.database import Base


class FavoriteModel(Base):
    """Таблица ``favorites``: закладка пользователя со snapshot-метаданными тайтла."""

    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    anime_id = Column(Integer, nullable=False)
    title = Column(String, nullable=True)
    original_title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    cover_url = Column(String, nullable=True)
    genres_json = Column(String, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)
