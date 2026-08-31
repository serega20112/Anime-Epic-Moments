"""Record that the user finished watching an episode."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CompleteEpisodeCommand:
    """Advance the user's progress after finishing an episode.

    Attributes:
        user_id: Acting user identifier.
        anime_id: Anime identifier.
        episode: Episode number that was finished.
    """

    user_id: int
    anime_id: int
    episode: int
