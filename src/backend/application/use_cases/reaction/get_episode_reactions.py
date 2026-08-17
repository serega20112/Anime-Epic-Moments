from backend.application.dto import GetEpisodeReactionsQuery
from backend.application.use_cases.reaction.result import ReactionResult
from backend.domain import ReactionRepository
from backend.domain.reaction.value_object import EpisodeReactionSummary


class GetEpisodeReactionsUseCase:
    """Aggregates reaction state for an episode and a viewer."""

    def __init__(self, reaction_repo: ReactionRepository):
        self.reaction_repo = reaction_repo

    async def execute(self, query: GetEpisodeReactionsQuery) -> ReactionResult:
        """Read reaction counts and the viewer's own reaction.

        Args:
            query: Reaction query parameters.

        Returns:
            ReactionResult: Aggregated reaction summary.
        """
        if query.episode <= 0:
            return await ReactionResult.failure("invalid_episode", status_code=400)
        counts = await self.reaction_repo.get_reaction_counts(query.anime_id, query.episode)
        user_reaction = None
        if query.user_id is not None:
            current = await self.reaction_repo.get_user_reaction(
                query.user_id,
                query.anime_id,
                query.episode,
            )
            if current is not None:
                user_reaction = current.reaction_type
        return await ReactionResult.success(
            EpisodeReactionSummary(counts=counts, user_reaction=user_reaction)
        )
