"""Список коллекций пользователя."""

from backend.application.dto.collection.get_user_collections_query import GetUserCollectionsQuery
from backend.application.interface.repositories.collection_repository import CollectionRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain.value_objects.collection.cards import (
    CollectionCard,
    CollectionDetails,
    CollectionItemCard,
)


class GetUserCollectionsUseCase:
    """Собирает коллекции пользователя для личной страницы."""

    def __init__(self, uow: UnitOfWorkInterface) -> None:
        """Инициализирует сценарий получения коллекций пользователя.

        Args:
            uow: Единица работы, через которую берётся репозиторий.
        """
        self._uow = uow

    async def execute(self, query: GetUserCollectionsQuery) -> list[CollectionDetails]:
        """Возвращает коллекции пользователя в виде карточек.

        Args:
            query: Запрос с идентификатором пользователя.

        Returns:
            list[CollectionDetails]: Список карточек коллекций.
        """
        async with self._uow as uow:
            repository = uow.repository(CollectionRepository)
            collections = await repository.get_user_collections(query.user_id)
            counts = await repository.get_items_count_map(
                [item.id for item in collections if item.id is not None]
            )
            result: list[CollectionDetails] = []
            for collection in collections:
                if collection.id is None:
                    continue
                items = await repository.get_items(collection.id)
                result.append(
                    CollectionDetails(
                        collection=CollectionCard(
                            id=collection.id,
                            title=collection.title,
                            description=collection.description,
                            items_count=counts.get(collection.id, len(items)),
                            is_public=collection.is_public,
                            created_at=collection.created_at.strftime("%Y-%m-%d"),
                            share_url=f"/collections/share/{collection.id}",
                            cover_url=collection.cover_url,
                        ),
                        items=[
                            CollectionItemCard(
                                anime_id=item.anime_id,
                                title=item.title,
                                description=item.description,
                                cover_url=item.cover_url,
                                genres=item.genres,
                                watch_url=f"/watch/{item.anime_id}?episode=1",
                                original_title=item.original_title,
                            )
                            for item in items
                        ],
                    )
                )
            return result
