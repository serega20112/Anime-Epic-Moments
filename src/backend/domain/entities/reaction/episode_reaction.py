"""Сущность реакции на эпизод."""

from datetime import datetime

from backend.domain.value_objects.reaction.reaction_type import EpisodeReactionType


class EpisodeReaction:
    """A user's reaction attached to a moment inside an episode."""

    def __init__(
        self,
        user_id: int,
        anime_id: int,
        episode: int,
        reaction_type: EpisodeReactionType,
        timestamp: float = 0.0,
        id: int | None = None,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.user_id = user_id
        self.anime_id = anime_id
        self.episode = episode
        self.reaction_type = reaction_type
        self.timestamp = timestamp
        self.created_at = created_at or datetime.utcnow()
