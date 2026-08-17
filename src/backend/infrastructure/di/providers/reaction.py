"""Reaction use case providers."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.use_cases import (
    GetEpisodeReactionsUseCase,
    SetEpisodeReactionUseCase,
)
from backend.infrastructure.repositories.reaction_repository import ReactionRepository


class ReactionUseCaseProvider(Provider):
    """Provide episode reaction use cases."""

    @provide(scope=Scope.REQUEST)
    async def get_episode_reactions(
        self,
        reaction_repository: ReactionRepository,
    ) -> GetEpisodeReactionsUseCase:
        """Provide the get episode reactions use case.

        Args:
            reaction_repository: Reaction repository.

        Returns:
            GetEpisodeReactionsUseCase: Configured use case.
        """
        return GetEpisodeReactionsUseCase(reaction_repository)

    @provide(scope=Scope.REQUEST)
    async def set_episode_reaction(
        self,
        reaction_repository: ReactionRepository,
    ) -> SetEpisodeReactionUseCase:
        """Provide the set episode reaction use case.

        Args:
            reaction_repository: Reaction repository.

        Returns:
            SetEpisodeReactionUseCase: Configured use case.
        """
        return SetEpisodeReactionUseCase(reaction_repository)
