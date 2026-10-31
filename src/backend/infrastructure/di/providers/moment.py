"""Провайдеры сценариев моментов просмотра."""

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


class MomentUseCaseProvider(Provider):
    """Провайдер сценариев моментов просмотра."""

    @provide(scope=Scope.REQUEST)
    async def save_viewing_moment(
        self,
        unit_of_work: UnitOfWorkInterface,
    ) -> SaveViewingMomentUseCase:
        """Создать сценарий сохранения черновика момента."""
        return SaveViewingMomentUseCase(unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def publish_viewing_moment(
        self,
        unit_of_work: UnitOfWorkInterface,
        create_highlight: CreateHighlightUseCase,
    ) -> PublishViewingMomentUseCase:
        """Создать сценарий публикации момента."""
        return PublishViewingMomentUseCase(unit_of_work, create_highlight)

    @provide(scope=Scope.REQUEST)
    async def get_user_viewing_moments(
        self,
        unit_of_work: UnitOfWorkInterface,
    ) -> GetUserViewingMomentsUseCase:
        """Создать сценарий списка моментов пользователя."""
        return GetUserViewingMomentsUseCase(unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def delete_viewing_moment(
        self,
        unit_of_work: UnitOfWorkInterface,
    ) -> DeleteViewingMomentUseCase:
        """Создать сценарий удаления черновика момента."""
        return DeleteViewingMomentUseCase(unit_of_work)
