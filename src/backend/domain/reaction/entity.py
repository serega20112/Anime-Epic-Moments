"""Episode reaction entities and the reaction type enum."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum


class EpisodeReactionType(StrEnum):
    """Reaction types a user can attach to a specific episode moment."""

    FIRE = "fire"
    LOVE = "love"
    LAUGH = "laugh"
    CRY = "cry"
    SHOCK = "shock"
    SKULL = "skull"
    SPARKLE = "sparkle"

    @classmethod
    async def from_value(cls, value: str | None) -> EpisodeReactionType | None:
        """Resolve a reaction type from a raw string.

        Args:
            value: Raw reaction label.

        Returns:
            EpisodeReactionType | None: The matching type or None when unknown.
        """
        if not value:
            return None
        try:
            return cls(str(value).strip().lower())
        except ValueError:
            return None


EPISODE_REACTION_EMOJI: dict[EpisodeReactionType, str] = {
    EpisodeReactionType.FIRE: "🔥",
    EpisodeReactionType.LOVE: "❤️",
    EpisodeReactionType.LAUGH: "😂",
    EpisodeReactionType.CRY: "😭",
    EpisodeReactionType.SHOCK: "😱",
    EpisodeReactionType.SKULL: "💀",
    EpisodeReactionType.SPARKLE: "✨",
}


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
