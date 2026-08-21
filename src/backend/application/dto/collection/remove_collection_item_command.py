"""Remove anime item from a collection form payload."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RemoveCollectionItemCommand:
    """Remove anime item from a collection form payload.

    Attributes:
        collection_id: Target collection identifier.
        anime_id: Anime identifier to remove.
    """

    collection_id: int
    anime_id: int
