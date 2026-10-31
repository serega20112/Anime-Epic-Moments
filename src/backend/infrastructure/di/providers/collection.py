"""Провайдеры сценариев коллекций."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.interface.services import AnimeApiClientInterface
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases import (
    AddCollectionItemUseCase,
    GetUserCollectionsUseCase,
    RemoveCollectionItemUseCase,
)
from backend.application.use_cases.collection.create_collection import CreateCollectionUseCase
from backend.application.use_cases.collection.get_shared_collection import (
    GetSharedCollectionUseCase,
)


class CollectionUseCaseProvider(Provider):
    """Провайдер сценариев коллекций."""

    @provide(scope=Scope.REQUEST)
    async def create_collection(self, unit_of_work: UnitOfWorkInterface) -> CreateCollectionUseCase:
        """Создать сценарий создания коллекции."""
        return CreateCollectionUseCase(unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def add_collection_item(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClientInterface,
    ) -> AddCollectionItemUseCase:
        """Создать сценарий добавления аниме в коллекцию."""
        return AddCollectionItemUseCase(unit_of_work, anime_api_client)

    @provide(scope=Scope.REQUEST)
    async def remove_collection_item(
        self,
        unit_of_work: UnitOfWorkInterface,
    ) -> RemoveCollectionItemUseCase:
        """Создать сценарий удаления аниме из коллекции."""
        return RemoveCollectionItemUseCase(unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def get_user_collections(
        self,
        unit_of_work: UnitOfWorkInterface,
    ) -> GetUserCollectionsUseCase:
        """Создать сценарий списка коллекций пользователя."""
        return GetUserCollectionsUseCase(unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def get_shared_collection(
        self,
        unit_of_work: UnitOfWorkInterface,
    ) -> GetSharedCollectionUseCase:
        """Создать сценарий чтения коллекции по ссылке."""
        return GetSharedCollectionUseCase(unit_of_work)
