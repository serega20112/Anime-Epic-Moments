from backend.application.dto import AddCollectionItemCommand
from backend.application.interface.repositories.collection_repository import CollectionRepository
from backend.application.interface.services import AnimeApiClientInterface as AnimeApiClient
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain.entities.collection.collection_item import AnimeCollectionItem


class CollectionAccessError(PermissionError):
    """Raised when a user acts on a collection they do not own."""


class AddCollectionItemUseCase:
    """Добавляет аниме в пользовательскую коллекцию."""

    def __init__(
        self,
        collection_repo: CollectionRepository,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClient | None = None,
    ):
        self.collection_repo = collection_repo
        self.unit_of_work = unit_of_work
        self.anime_api_client = anime_api_client

    async def execute(self, command: AddCollectionItemCommand) -> AnimeCollectionItem:
        """Add an anime item to a collection within a transaction."""
        async with self.unit_of_work:
            return await self._execute(command)

    async def _execute(self, command: AddCollectionItemCommand) -> AnimeCollectionItem:
        """Add an anime item to a collection.

        The collection must belong to the acting user. When the caller did not
        provide a title snapshot, the anime is resolved through the anime API
        client so the stored snapshot carries the enriched Russian title.

        Args:
            command: Add collection item command.

        Returns:
            AnimeCollectionItem: Created collection item.

        Raises:
            CollectionAccessError: When the collection does not exist or
                belongs to another user.
        """
        collection = await self.collection_repo.get_by_id(command.collection_id)
        if collection is None:
            raise CollectionAccessError("Коллекция не найдена")
        if command.user_id is not None and collection.user_id != command.user_id:
            raise CollectionAccessError("Нет доступа к этой коллекции")

        snapshot = await self._resolve_snapshot(command)
        item = AnimeCollectionItem(
            collection_id=command.collection_id,
            anime_id=command.anime_id,
            title=snapshot["title"],
            description=snapshot["description"],
            cover_url=snapshot["cover_url"],
            genres=snapshot["genres"],
            original_title=snapshot["original_title"],
        )
        return await self.collection_repo.add_item(item)

    async def _resolve_snapshot(self, command: AddCollectionItemCommand) -> dict:
        """Build the item snapshot, fetching the anime when fields are missing.

        Args:
            command: Add collection item command.

        Returns:
            dict: Snapshot fields with command values taking priority.
        """
        snapshot = {
            "title": command.title,
            "description": command.description,
            "cover_url": command.cover_url,
            "genres": command.genres,
            "original_title": command.original_title,
        }
        if snapshot["title"] or self.anime_api_client is None:
            return snapshot
        anime = await self.anime_api_client.get_by_id(command.anime_id)
        if anime is None:
            return snapshot
        snapshot["title"] = anime.title or f"Anime #{command.anime_id}"
        snapshot["description"] = anime.description or ""
        snapshot["cover_url"] = anime.cover_url
        snapshot["genres"] = anime.genres or []
        snapshot["original_title"] = anime.original_title
        return snapshot
