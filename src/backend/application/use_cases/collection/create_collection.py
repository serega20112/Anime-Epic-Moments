from backend.application.dto import CreateCollectionCommand
from backend.application.interface.repositories.collection_repository import CollectionRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain.aggregates.collection.collection import AnimeCollection


class CreateCollectionUseCase:
    """Создает пользовательскую коллекцию аниме."""

    def __init__(
        self,
        collection_repo: CollectionRepository,
        unit_of_work: UnitOfWorkInterface,
    ):
        self.collection_repo = collection_repo
        self.unit_of_work = unit_of_work

    async def execute(self, command: CreateCollectionCommand) -> AnimeCollection:
        """Create a collection within a transaction."""
        async with self.unit_of_work:
            return await self._execute(command)

    async def _execute(self, command: CreateCollectionCommand) -> AnimeCollection:
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
            cover_url=command.cover_url,
        )
        return await self.collection_repo.create_collection(collection)
