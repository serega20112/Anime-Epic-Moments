"""Set or remove a reaction on an episode moment."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SetEpisodeReactionCommand:
    """Set or remove a reaction on an episode moment.

    Attributes:
        user_id: Acting user identifier.
        anime_id: Anime identifier.
        episode: Episode number.
        reaction_type: Reaction label, ignored when removing.
        timestamp: Playback position in seconds.
        liked: True to set the reaction, False to remove it.
    """

    user_id: int
    anime_id: int
    episode: int
    reaction_type: str
    timestamp: float = 0.0
    liked: bool = True
