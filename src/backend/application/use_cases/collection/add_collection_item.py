"""Сценарий добавления аниме в коллекцию."""

from backend.application.dto import AddCollectionItemCommand
from backend.application.interface.repositories.collection_repository import CollectionRepository
from backend.application.interface.services import AnimeApiClientInterface
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain.entities.collection.collection_item import AnimeCollectionItem
from backend.domain.exceptions import AuthorizationError


class CollectionAccessError(AuthorizationError):
    """Пользователь пытается изменить чужую коллекцию."""


class AddCollectionItemUseCase:
    """Добавляет аниме в пользовательскую коллекцию."""

    def __init__(self, uow: UnitOfWorkInterface, anime_api_client: AnimeApiClientInterface) -> None:
        """Инициализирует сценарий добавления элемента в коллекцию.

        Args:
            uow: Единица работы, через которую берётся репозиторий.
            anime_api_client: Клиент API аниме для обогащения снимка карточки.
        """
        self._uow = uow
        self._anime_api_client = anime_api_client

    async def execute(self, command: AddCollectionItemCommand) -> AnimeCollectionItem:
        """Добавляет элемент аниме в коллекцию внутри транзакции.

        Снимок карточки собирается до открытия транзакции: обращение к внешнему
        API не должно удерживать соединение с базой. Коллекция должна
        принадлежать выполняющему пользователю.

        Args:
            command: Команда добавления элемента коллекции.

        Returns:
            AnimeCollectionItem: Созданный элемент коллекции.

        Raises:
            CollectionAccessError: Когда коллекция не найдена или принадлежит
                другому пользователю.
        """
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
        async with self._uow as uow:
            repository = uow.repository(CollectionRepository)
            collection = await repository.get_by_id(command.collection_id)
            if collection is None:
                raise CollectionAccessError("Коллекция не найдена")
            if collection.user_id != command.user_id:
                raise CollectionAccessError("Нет доступа к этой коллекции")
            return await repository.add_item(item)

    async def _resolve_snapshot(self, command: AddCollectionItemCommand) -> dict:
        """Собрать снимок карточки, подгрузив аниме при нехватке полей.

        Args:
            command: Команда добавления элемента коллекции.

        Returns:
            dict: Поля карточки для сохранения снимка.
        """
        snapshot = {
            "title": command.title,
            "description": command.description,
            "cover_url": command.cover_url,
            "genres": command.genres,
            "original_title": command.original_title,
        }
        if snapshot["title"]:
            return snapshot
        anime = await self._anime_api_client.get_by_id(command.anime_id)
        if anime is None:
            return snapshot
        snapshot["title"] = anime.title or f"Anime #{command.anime_id}"
        snapshot["description"] = anime.description or ""
        snapshot["cover_url"] = anime.cover_url
        snapshot["genres"] = anime.genres or []
        snapshot["original_title"] = anime.original_title
        return snapshot
