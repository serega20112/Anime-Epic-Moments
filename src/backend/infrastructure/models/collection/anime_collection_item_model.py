"""SQLAlchemy-модель элемента коллекции аниме."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from backend.infrastructure.files.database import Base


class AnimeCollectionItemModel(Base):
    """Таблица ``anime_collection_items``: тайтл в коллекции со snapshot-метаданными."""

    __tablename__ = "anime_collection_items"
    __table_args__ = (UniqueConstraint("collection_id", "anime_id", name="uq_collection_anime"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_id = Column(
        Integer, ForeignKey("anime_collections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    anime_id = Column(Integer, nullable=False)
    title = Column(String(120), nullable=False)
    description = Column(String, nullable=True)
    cover_url = Column(String, nullable=True)
    genres_json = Column(String, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)
