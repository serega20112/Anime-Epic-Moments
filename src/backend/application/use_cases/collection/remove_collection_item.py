from backend.application.dto import RemoveCollectionItemCommand
from backend.domain.repositories.collection_repository import CollectionRepository
from backend.domain.unit_of_work import UnitOfWorkInterface


class RemoveCollectionItemUseCase:
    """Удаляет аниме из пользовательской коллекции."""

    def __init__(
            self,
            collection_repo: CollectionRepository,
            unit_of_work: UnitOfWorkInterface | None = None,
    ):
        self.collection_repo = collection_repo
        self.unit_of_work = unit_of_work

    async def execute(self, command: RemoveCollectionItemCommand) -> None:
        """Remove an anime item from a collection within a transaction if configured."""
        if self.unit_of_work is None:
            await self._execute(command)
            return
        async with self.unit_of_work:
            await self._execute(command)

    async def _execute(self, command: RemoveCollectionItemCommand) -> None:
        """Remove an anime item from a collection.

        Args:
            command: Remove collection item command.
        """
        await self.collection_repo.remove_item(
            collection_id=command.collection_id, anime_id=command.anime_id
        )
