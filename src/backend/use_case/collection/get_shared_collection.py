from src.backend.domain.collection.value_object import (
    CollectionCard,
    CollectionDetails,
    CollectionItemCard,
)
from src.backend.repository.collection_repository import CollectionRepository


class GetSharedCollectionUseCase:
    """Возвращает публичную коллекцию аниме для share-страницы."""

    def __init__(self, collection_repo: CollectionRepository):
        self.collection_repo = collection_repo

    def execute(self, collection_id: int) -> CollectionDetails:
        collection = self.collection_repo.get_by_id(collection_id)
        if collection is None or (not collection.is_public):
            raise ValueError("Коллекция не найдена")
        items = self.collection_repo.get_items(collection_id)
        return CollectionDetails(
            collection=CollectionCard(
                id=collection.id or collection_id,
                title=collection.title,
                description=collection.description,
                items_count=len(items),
                is_public=collection.is_public,
                created_at=collection.created_at.strftime("%Y-%m-%d"),
                share_url=f"/collections/share/{collection.id or collection_id}",
            ),
            items=[
                CollectionItemCard(
                    anime_id=item.anime_id,
                    title=item.title,
                    description=item.description,
                    cover_url=item.cover_url,
                    genres=item.genres,
                    watch_url=f"/watch/{item.anime_id}?episode=1",
                )
                for item in items
            ],
        )
