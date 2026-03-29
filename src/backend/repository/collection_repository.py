from abc import ABC, abstractmethod

from src.backend.domain.collection.entity import AnimeCollection, AnimeCollectionItem


class CollectionRepository(ABC):
    @abstractmethod
    def create_collection(self, collection: AnimeCollection) -> AnimeCollection:
        """Создает коллекцию пользователя."""

    @abstractmethod
    def get_by_id(self, collection_id: int) -> AnimeCollection | None:
        """Возвращает коллекцию по id."""

    @abstractmethod
    def get_user_collections(self, user_id: int) -> list[AnimeCollection]:
        """Возвращает коллекции пользователя."""

    @abstractmethod
    def get_public_user_collections(self, user_id: int) -> list[AnimeCollection]:
        """Возвращает публичные коллекции пользователя."""

    @abstractmethod
    def add_item(self, item: AnimeCollectionItem) -> AnimeCollectionItem:
        """Добавляет аниме в коллекцию пользователя."""

    @abstractmethod
    def remove_item(self, collection_id: int, anime_id: int) -> None:
        """Удаляет аниме из коллекции."""

    @abstractmethod
    def get_items(self, collection_id: int) -> list[AnimeCollectionItem]:
        """Возвращает элементы коллекции."""
