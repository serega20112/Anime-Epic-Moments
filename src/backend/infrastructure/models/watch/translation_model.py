"""SQLAlchemy-модель озвучки (перевода) аниме."""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
)

from backend.infrastructure.files.database import Base


class TranslationModel(Base):
    """Таблица ``translations``: логическая озвучка/перевод тайтла."""

    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    anime_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    translation_type = Column(String, nullable=False)
    language = Column(String, nullable=False, default="ru")
    created_at = Column(DateTime, default=datetime.utcnow)
