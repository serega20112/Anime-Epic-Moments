"""Upsert the user's watch status for an anime."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UpsertUserAnimeStatusCommand:
    """Upsert the user's watch status for an anime.

    Attributes:
        user_id: Acting user identifier.
        anime_id: Anime identifier.
        status: Watch status label.
        current_episode: Episode reached by the user.
        rating: Optional personal rating.
        note: Optional personal note.
        started_at: Optional ISO start date.
        completed_at: Optional ISO completion date.
    """

    user_id: int
    anime_id: int
    status: str
    current_episode: int | None = None
    rating: float | None = None
    note: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
