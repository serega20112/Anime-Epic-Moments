from backend.application.dto import AddCollectionItemCommand
from backend.domain.collection.entity import AnimeCollectionItem
from backend.domain.repositories.collection_repository import CollectionRepository


class AddCollectionItemUseCase:
    """Добавляет аниме в пользовательскую коллекцию."""

    def __init__(self, collection_repo: CollectionRepository):
        self.collection_repo = collection_repo

    async def execute(self, command: AddCollectionItemCommand) -> AnimeCollectionItem:
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
        )
        return await self.collection_repo.add_item(item)
