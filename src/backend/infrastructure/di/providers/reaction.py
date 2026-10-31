"""Провайдеры сценариев реакций на серии."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases import (
    GetEpisodeReactionsUseCase,
    SetEpisodeReactionUseCase,
)


class ReactionUseCaseProvider(Provider):
    """Провайдер сценариев реакций на серии."""

    @provide(scope=Scope.REQUEST)
    async def get_episode_reactions(
        self,
        unit_of_work: UnitOfWorkInterface,
    ) -> GetEpisodeReactionsUseCase:
        """Создать сценарий сводки реакций на серию."""
        return GetEpisodeReactionsUseCase(unit_of_work)

    @provide(scope=Scope.REQUEST)
    async def set_episode_reaction(
        self,
        unit_of_work: UnitOfWorkInterface,
    ) -> SetEpisodeReactionUseCase:
        """Создать сценарий смены реакции на серию."""
        return SetEpisodeReactionUseCase(unit_of_work)
