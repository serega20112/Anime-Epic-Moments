from backend.domain.collection.value_object import (
    CollectionCard,
    CollectionDetails,
    CollectionItemCard,
)
from backend.domain.repositories.collection_repository import CollectionRepository


class GetUserCollectionsUseCase:
    """Собирает коллекции пользователя для личной страницы."""

    def __init__(self, collection_repo: CollectionRepository):
        self.collection_repo = collection_repo

    async def execute(self, user_id: int) -> list[CollectionDetails]:
        collections = await self.collection_repo.get_user_collections(user_id)
        counts = await self.collection_repo.get_items_count_map(
            [item.id for item in collections if item.id is not None]
        )
        result: list[CollectionDetails] = []
        for collection in collections:
            if collection.id is None:
                continue
            items = await self.collection_repo.get_items(collection.id)
            result.append(
                CollectionDetails(
                    collection=CollectionCard(
                        id=collection.id,
                        title=collection.title,
                        description=collection.description,
                        items_count=counts.get(collection.id, len(items)),
                        is_public=collection.is_public,
                        created_at=collection.created_at.strftime("%Y-%m-%d"),
                        share_url=f"/collections/share/{collection.id}",
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
            )
        return result
