"""Query parameters for reading an episode's reaction state."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetEpisodeReactionsQuery:
    """Query parameters for reading an episode's reaction state.

    Attributes:
        anime_id: Anime identifier.
        episode: Episode number.
        user_id: Optional viewer for their own reaction.
    """

    anime_id: int
    episode: int
    user_id: int | None = None
