from backend.application.dto import CreateCollectionCommand
from backend.domain.collection.entity import AnimeCollection
from backend.domain.repositories.collection_repository import CollectionRepository
from backend.domain.unit_of_work import UnitOfWorkInterface


class CreateCollectionUseCase:
    """Создает пользовательскую коллекцию аниме."""

    def __init__(
            self,
            collection_repo: CollectionRepository,
            unit_of_work: UnitOfWorkInterface | None = None,
    ):
        self.collection_repo = collection_repo
        self.unit_of_work = unit_of_work

    async def execute(self, command: CreateCollectionCommand) -> AnimeCollection:
        """Create a collection within a transaction if configured."""
        if self.unit_of_work is None:
            return await self._execute(command)
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
        )
        return await self.collection_repo.create_collection(collection)
