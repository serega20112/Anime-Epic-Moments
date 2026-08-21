"""SQLAlchemy-модели зоны «Коллекции»: пользовательские подборки тайтлов."""

from backend.infrastructure.models.collection.anime_collection_item_model import (
    AnimeCollectionItemModel,
)
from backend.infrastructure.models.collection.anime_collection_model import AnimeCollectionModel

__all__ = ["AnimeCollectionItemModel", "AnimeCollectionModel"]
