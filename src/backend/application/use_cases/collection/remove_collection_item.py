from backend.application.dto import RemoveCollectionItemCommand
from backend.domain.repositories.collection_repository import CollectionRepository


class RemoveCollectionItemUseCase:
    """Удаляет аниме из пользовательской коллекции."""

    def __init__(self, collection_repo: CollectionRepository):
        self.collection_repo = collection_repo

    async def execute(self, command: RemoveCollectionItemCommand) -> None:
        """Remove an anime item from a collection.

        Args:
            command: Remove collection item command.
        """
        await self.collection_repo.remove_item(
            collection_id=command.collection_id, anime_id=command.anime_id
        )
