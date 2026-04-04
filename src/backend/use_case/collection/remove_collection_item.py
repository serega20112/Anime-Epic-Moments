from src.backend.repository.collection_repository import CollectionRepository


class RemoveCollectionItemUseCase:
    """Удаляет аниме из пользовательской коллекции."""

    def __init__(self, collection_repo: CollectionRepository):
        self.collection_repo = collection_repo

    async def execute(self, collection_id: int, anime_id: int) -> None:
        await self.collection_repo.remove_item(collection_id=collection_id, anime_id=anime_id)
