from starlette import status

from backend.application.dto import SetEpisodeReactionCommand
from backend.application.interface.repositories.reaction_repository import ReactionRepository
from backend.application.use_cases.reaction.result import ReactionResult
from backend.domain import EpisodeReaction, EpisodeReactionType
from backend.domain.value_objects.reaction.reaction_summary import EpisodeReactionSummary


class SetEpisodeReactionUseCase:
    """Sets or removes a user's reaction on an episode."""

    def __init__(self, reaction_repo: ReactionRepository):
        self.reaction_repo = reaction_repo

    async def execute(self, command: SetEpisodeReactionCommand) -> ReactionResult:
        """Apply the reaction and return the updated episode state.

        Args:
            command: Set episode reaction command.

        Returns:
            ReactionResult: Updated reaction summary.
        """
        if command.episode <= 0:
            return await ReactionResult.failure(
                "invalid_episode", status_code=status.HTTP_400_BAD_REQUEST
            )

        reaction_type = EpisodeReactionType.from_value(command.reaction_type)
        if not command.liked:
            await self.reaction_repo.remove_reaction(
                command.user_id,
                command.anime_id,
                command.episode,
            )
        elif reaction_type is None:
            return await ReactionResult.failure(
                "invalid_reaction_type", status_code=status.HTTP_400_BAD_REQUEST
            )
        else:
            await self.reaction_repo.set_reaction(
                EpisodeReaction(
                    user_id=command.user_id,
                    anime_id=command.anime_id,
                    episode=command.episode,
                    reaction_type=reaction_type,
                    timestamp=command.timestamp,
                )
            )

        counts = await self.reaction_repo.get_reaction_counts(command.anime_id, command.episode)
        current = await self.reaction_repo.get_user_reaction(
            command.user_id,
            command.anime_id,
            command.episode,
        )
        return await ReactionResult.success(
            EpisodeReactionSummary(
                counts=counts,
                user_reaction=current.reaction_type if current else None,
            )
        )
