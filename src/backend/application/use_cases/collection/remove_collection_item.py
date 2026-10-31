"""Сценарий удаления аниме из пользовательской коллекции."""

from backend.application.dto import RemoveCollectionItemCommand
from backend.application.interface.repositories.collection_repository import CollectionRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.collection.add_collection_item import CollectionAccessError
from backend.domain.exceptions import AuthorizationError


class RemoveCollectionItemUseCase:
    """Удаляет аниме из коллекции её владельцем."""

    def __init__(self, uow: UnitOfWorkInterface) -> None:
        """Инициализирует сценарий удаления элемента коллекции.

        Args:
            uow: Единица работы, через которую берётся репозиторий.
        """
        self._uow = uow

    async def execute(self, command: RemoveCollectionItemCommand) -> None:
        """Проверяет права и удаляет элемент коллекции внутри транзакции.

        Args:
            command: Команда удаления.

        Raises:
            CollectionAccessError: Коллекция не найдена или принадлежит
                другому пользователю.
        """
        async with self._uow as uow:
            repository = uow.repository(CollectionRepository)
            collection = await repository.get_by_id(command.collection_id)
            if collection is None:
                raise CollectionAccessError("Коллекция не найдена")
            try:
                collection.ensure_owned_by(command.user_id)
            except AuthorizationError as error:
                raise CollectionAccessError(str(error)) from error
            await repository.remove_item(
                collection_id=command.collection_id,
                anime_id=command.anime_id,
            )
