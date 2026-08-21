from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities.reaction.episode_reaction import EpisodeReaction
from backend.domain.value_objects.reaction.reaction_summary import EpisodeReactionCount
from backend.domain.value_objects.reaction.reaction_type import EpisodeReactionType
from backend.infrastructure.models import EpisodeReactionModel


class ReactionRepository:
    """Data access for episode reactions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def set_reaction(self, reaction: EpisodeReaction) -> EpisodeReaction:
        """Create or update a user's reaction on an episode.

        Args:
            reaction: Reaction aggregate to persist.

        Returns:
            EpisodeReaction: The persisted reaction.
        """
        result = await self.session.execute(
            select(EpisodeReactionModel).where(
                EpisodeReactionModel.user_id == reaction.user_id,
                EpisodeReactionModel.anime_id == reaction.anime_id,
                EpisodeReactionModel.episode == reaction.episode,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            row.reaction_type = reaction.reaction_type.value
            row.timestamp = reaction.timestamp
            await self.session.flush()
            reaction.id = row.id
            reaction.created_at = row.created_at
            return reaction

        row = EpisodeReactionModel(
            user_id=reaction.user_id,
            anime_id=reaction.anime_id,
            episode=reaction.episode,
            reaction_type=reaction.reaction_type.value,
            timestamp=reaction.timestamp,
        )
        self.session.add(row)
        await self.session.flush()
        reaction.id = row.id
        reaction.created_at = row.created_at
        return reaction

    async def remove_reaction(self, user_id: int, anime_id: int, episode: int) -> bool:
        """Remove a user's reaction on an episode.

        Args:
            user_id: User identifier.
            anime_id: Anime identifier.
            episode: Episode number.

        Returns:
            bool: True when a reaction was removed.
        """
        result = await self.session.execute(
            delete(EpisodeReactionModel).where(
                EpisodeReactionModel.user_id == user_id,
                EpisodeReactionModel.anime_id == anime_id,
                EpisodeReactionModel.episode == episode,
            )
        )
        await self.session.flush()
        return result.rowcount > 0

    async def get_reaction_counts(
        self,
        anime_id: int,
        episode: int,
    ) -> list[EpisodeReactionCount]:
        """Count reactions per type for an episode.

        Args:
            anime_id: Anime identifier.
            episode: Episode number.

        Returns:
            list[EpisodeReactionCount]: Counts per reaction type.
        """
        result = await self.session.execute(
            select(
                EpisodeReactionModel.reaction_type,
                func.count(EpisodeReactionModel.id),
            )
            .where(
                EpisodeReactionModel.anime_id == anime_id,
                EpisodeReactionModel.episode == episode,
            )
            .group_by(EpisodeReactionModel.reaction_type)
        )
        counts: list[EpisodeReactionCount] = []
        for raw_type, count in result.all():
            reaction_type = await EpisodeReactionType.from_value(raw_type)
            if reaction_type is not None:
                counts.append(EpisodeReactionCount(reaction_type=reaction_type, count=int(count)))
        return counts

    async def get_user_reaction(
        self,
        user_id: int,
        anime_id: int,
        episode: int,
    ) -> EpisodeReaction | None:
        """Fetch the current reaction of a user on an episode.

        Args:
            user_id: User identifier.
            anime_id: Anime identifier.
            episode: Episode number.

        Returns:
            EpisodeReaction | None: The reaction or None when missing.
        """
        result = await self.session.execute(
            select(EpisodeReactionModel).where(
                EpisodeReactionModel.user_id == user_id,
                EpisodeReactionModel.anime_id == anime_id,
                EpisodeReactionModel.episode == episode,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        reaction_type = await EpisodeReactionType.from_value(row.reaction_type)
        if reaction_type is None:
            return None
        return EpisodeReaction(
            id=row.id,
            user_id=row.user_id,
            anime_id=row.anime_id,
            episode=row.episode,
            reaction_type=reaction_type,
            timestamp=row.timestamp,
            created_at=row.created_at,
        )
