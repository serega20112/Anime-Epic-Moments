from src.backend.domain.collection.entity import AnimeCollectionItem
from src.backend.repository.collection_repository import CollectionRepository


class AddCollectionItemUseCase:
    """Добавляет аниме в пользовательскую коллекцию."""

    def __init__(self, collection_repo: CollectionRepository):
        self.collection_repo = collection_repo

    def execute(
        self,
        collection_id: int,
        anime_id: int,
        title: str,
        description: str = "",
        cover_url: str | None = None,
        genres: list[str] | None = None,
    ) -> AnimeCollectionItem:
        item = AnimeCollectionItem(
            collection_id=collection_id,
            anime_id=anime_id,
            title=title,
            description=description,
            cover_url=cover_url,
            genres=genres,
        )
        return self.collection_repo.add_item(item)
