"""Collection use case providers."""

from __future__ import annotations

from dishka import Provider, Scope, provide

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
from backend.infrastructure.repositories.collection_repository import CollectionRepository


class CollectionUseCaseProvider(Provider):
    """Provide collection use cases."""

    @provide(scope=Scope.REQUEST)
    async def create_collection(
        self,
        collection_repository: CollectionRepository,
        unit_of_work: UnitOfWorkInterface,
    ) -> CreateCollectionUseCase:
        """Provide the create collection use case.

        Args:
            collection_repository: Collection repository.
            unit_of_work: Transaction boundary.

        Returns:
            CreateCollectionUseCase: Configured use case.
        """
        return CreateCollectionUseCase(collection_repository, unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def add_collection_item(
        self,
        collection_repository: CollectionRepository,
        unit_of_work: UnitOfWorkInterface,
    ) -> AddCollectionItemUseCase:
        """Provide the add collection item use case.

        Args:
            collection_repository: Collection repository.
            unit_of_work: Transaction boundary.

        Returns:
            AddCollectionItemUseCase: Configured use case.
        """
        return AddCollectionItemUseCase(collection_repository, unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def remove_collection_item(
        self,
        collection_repository: CollectionRepository,
        unit_of_work: UnitOfWorkInterface,
    ) -> RemoveCollectionItemUseCase:
        """Provide the remove collection item use case.

        Args:
            collection_repository: Collection repository.
            unit_of_work: Transaction boundary.

        Returns:
            RemoveCollectionItemUseCase: Configured use case.
        """
        return RemoveCollectionItemUseCase(collection_repository, unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def get_user_collections(
        self,
        collection_repository: CollectionRepository,
    ) -> GetUserCollectionsUseCase:
        """Provide the get user collections use case.

        Args:
            collection_repository: Collection repository.

        Returns:
            GetUserCollectionsUseCase: Configured use case.
        """
        return GetUserCollectionsUseCase(collection_repository)

    @provide(scope=Scope.REQUEST)
    async def get_shared_collection(
        self,
        collection_repository: CollectionRepository,
    ) -> GetSharedCollectionUseCase:
        """Provide the get shared collection use case.

        Args:
            collection_repository: Collection repository.

        Returns:
            GetSharedCollectionUseCase: Configured use case.
        """
        return GetSharedCollectionUseCase(collection_repository)
