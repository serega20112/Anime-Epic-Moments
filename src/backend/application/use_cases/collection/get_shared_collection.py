"""Чтение коллекции по ссылке для общего доступа."""

from backend.application.dto.collection.get_shared_collection_query import GetSharedCollectionQuery
from backend.application.interface.repositories.collection_repository import CollectionRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain.value_objects.collection.cards import (
    CollectionCard,
    CollectionDetails,
    CollectionItemCard,
)


class GetSharedCollectionUseCase:
    """Возвращает публичную коллекцию аниме для share-страницы."""

    def __init__(self, uow: UnitOfWorkInterface) -> None:
        """Инициализирует сценарий получения общей коллекции.

        Args:
            uow: Единица работы, через которую берётся репозиторий.
        """
        self._uow = uow

    async def execute(self, query: GetSharedCollectionQuery) -> CollectionDetails:
        """Возвращает общую коллекцию по её идентификатору.

        Args:
            query: Запрос с идентификатором коллекции.

        Returns:
            CollectionDetails: Детали коллекции.

        Raises:
            ValueError: Когда коллекция не найдена или не является публичной.
        """
        async with self._uow as uow:
            repository = uow.repository(CollectionRepository)
            collection = await repository.get_by_id(query.collection_id)
            if collection is None or not collection.is_public:
                raise ValueError("Коллекция не найдена")
            items = await repository.get_items(query.collection_id)
            return CollectionDetails(
                collection=CollectionCard(
                    id=collection.id or query.collection_id,
                    title=collection.title,
                    description=collection.description,
                    items_count=len(items),
                    is_public=collection.is_public,
                    created_at=collection.created_at.strftime("%Y-%m-%d"),
                    share_url=f"/collections/share/{collection.id or query.collection_id}",
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
