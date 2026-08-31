from backend.application.dto import AddCollectionItemCommand
from backend.application.interface.repositories.collection_repository import CollectionRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain.entities.collection.collection_item import AnimeCollectionItem


class AddCollectionItemUseCase:
    """Добавляет аниме в пользовательскую коллекцию."""

    def __init__(
        self,
        collection_repo: CollectionRepository,
        unit_of_work: UnitOfWorkInterface,
    ):
        self.collection_repo = collection_repo
        self.unit_of_work = unit_of_work

    async def execute(self, command: AddCollectionItemCommand) -> AnimeCollectionItem:
        """Add an anime item to a collection within a transaction."""
        async with self.unit_of_work:
            return await self._execute(command)

    async def _execute(self, command: AddCollectionItemCommand) -> AnimeCollectionItem:
        """Add an anime item to a collection.

        Args:
            command: Add collection item command.

        Returns:
            AnimeCollectionItem: Created collection item.
        """
        item = AnimeCollectionItem(
            collection_id=command.collection_id,
            anime_id=command.anime_id,
            title=command.title,
            description=command.description,
            cover_url=command.cover_url,
            genres=command.genres,
            original_title=command.original_title,
        )
        return await self.collection_repo.add_item(item)
