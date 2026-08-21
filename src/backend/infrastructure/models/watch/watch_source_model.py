"""SQLAlchemy-модель источника просмотра."""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)

from backend.infrastructure.files.database import Base


class WatchSourceModel(Base):
    """Таблица ``watch_sources``: конкретный playable-источник серии от провайдера."""

    __tablename__ = "watch_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    anime_id = Column(Integer, nullable=False)
    episode = Column(Integer, nullable=False)
    translation_id = Column(
        Integer, ForeignKey("translations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_name = Column(String, nullable=False)
    source_name = Column(String, nullable=False)
    stream_url = Column(String, nullable=False)
    quality_label = Column(String, nullable=False)
    source_type = Column(String, nullable=False, default="stream")
    created_at = Column(DateTime, default=datetime.utcnow)
