"""Создание коллекции аниме."""

from backend.application.dto import CreateCollectionCommand
from backend.application.interface.repositories.collection_repository import CollectionRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain.aggregates.collection.collection import AnimeCollection


class CreateCollectionUseCase:
    """Создает пользовательскую коллекцию аниме."""

    def __init__(self, uow: UnitOfWorkInterface) -> None:
        """Инициализирует сценарий создания коллекции.

        Args:
            uow: Единица работы, через которую берётся репозиторий.
        """
        self._uow = uow

    async def execute(self, command: CreateCollectionCommand) -> AnimeCollection:
        """Создаёт коллекцию внутри транзакции.

        Args:
            command: Команда создания коллекции.

        Returns:
            AnimeCollection: Созданная коллекция.
        """
        collection = AnimeCollection(
            user_id=command.user_id,
            title=command.title,
            description=command.description,
            is_public=command.is_public,
            cover_url=command.cover_url,
        )
        async with self._uow as uow:
            return await uow.repository(CollectionRepository).create_collection(collection)
