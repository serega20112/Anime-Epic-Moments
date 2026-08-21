"""Viewing moment use case providers."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases import (
    DeleteViewingMomentUseCase,
    GetUserViewingMomentsUseCase,
    PublishViewingMomentUseCase,
    SaveViewingMomentUseCase,
)
from backend.application.use_cases.highlight.crud.create_highlight import CreateHighlightUseCase
from backend.infrastructure.repositories.moment_repository import MomentRepository


class MomentUseCaseProvider(Provider):
    """Provide viewing moment use cases."""

    @provide(scope=Scope.REQUEST)
    async def save_viewing_moment(
        self,
        moment_repository: MomentRepository,
        unit_of_work: UnitOfWorkInterface,
    ) -> SaveViewingMomentUseCase:
        """Provide the save viewing moment use case.

        Args:
            moment_repository: Moment repository.
            unit_of_work: Transaction boundary.

        Returns:
            SaveViewingMomentUseCase: Configured use case.
        """
        return SaveViewingMomentUseCase(moment_repository, unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def publish_viewing_moment(
        self,
        moment_repository: MomentRepository,
        create_highlight: CreateHighlightUseCase,
        unit_of_work: UnitOfWorkInterface,
    ) -> PublishViewingMomentUseCase:
        """Provide the publish viewing moment use case.

        Args:
            moment_repository: Moment repository.
            create_highlight: Create highlight use case.
            unit_of_work: Transaction boundary.

        Returns:
            PublishViewingMomentUseCase: Configured use case.
        """
        return PublishViewingMomentUseCase(moment_repository, create_highlight, unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def get_user_viewing_moments(
        self,
        moment_repository: MomentRepository,
    ) -> GetUserViewingMomentsUseCase:
        """Provide the get user viewing moments use case.

        Args:
            moment_repository: Moment repository.

        Returns:
            GetUserViewingMomentsUseCase: Configured use case.
        """
        return GetUserViewingMomentsUseCase(moment_repository)

    @provide(scope=Scope.REQUEST)
    async def delete_viewing_moment(
        self,
        moment_repository: MomentRepository,
        unit_of_work: UnitOfWorkInterface,
    ) -> DeleteViewingMomentUseCase:
        """Provide the delete viewing moment use case.

        Args:
            moment_repository: Moment repository.
            unit_of_work: Transaction boundary.

        Returns:
            DeleteViewingMomentUseCase: Configured use case.
        """
        return DeleteViewingMomentUseCase(moment_repository, unit_of_work)
