from backend.application.dto import CreateCollectionCommand
from backend.domain.collection.entity import AnimeCollection
from backend.domain.repositories.collection_repository import CollectionRepository


class CreateCollectionUseCase:
    """Создает пользовательскую коллекцию аниме."""

    def __init__(self, collection_repo: CollectionRepository):
        self.collection_repo = collection_repo

    async def execute(self, command: CreateCollectionCommand) -> AnimeCollection:
        """Create a new collection.

        Args:
            command: Create collection command.

        Returns:
            AnimeCollection: Created collection.
        """
        collection = AnimeCollection(
            user_id=command.user_id,
            title=command.title,
            description=command.description,
            is_public=command.is_public,
        )
        return await self.collection_repo.create_collection(collection)
