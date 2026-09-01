"""Add anime item to a collection form payload."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AddCollectionItemCommand:
    """Add anime item to a collection form payload.

    Attributes:
        user_id: Acting user identifier, used for the ownership check.
        collection_id: Target collection identifier.
        anime_id: Anime identifier to add.
        title: Anime title snapshot.
        description: Optional item description.
        cover_url: Optional anime cover URL.
        genres: Anime genres list.
        original_title: Original (non-Russian) anime title.
    """

    collection_id: int
    anime_id: int
    user_id: int | None = None
    title: str = ""
    description: str = ""
    cover_url: str | None = None
    genres: list[str] = field(default_factory=list)
    original_title: str | None = None
