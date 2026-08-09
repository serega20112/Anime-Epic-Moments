"""Data transfer objects for anime collection commands."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CreateCollectionCommand:
    """Create collection form payload.

    Attributes:
        user_id: Owner user identifier.
        title: Collection title.
        description: Optional collection description.
        is_public: Whether the collection is publicly visible.
    """

    user_id: int
    title: str
    description: str = ""
    is_public: bool = True


@dataclass(frozen=True, slots=True)
class AddCollectionItemCommand:
    """Add anime item to a collection form payload.

    Attributes:
        collection_id: Target collection identifier.
        anime_id: Anime identifier to add.
        title: Anime title snapshot.
        description: Optional item description.
        cover_url: Optional anime cover URL.
        genres: Anime genres list.
    """

    collection_id: int
    anime_id: int
    title: str
    description: str = ""
    cover_url: str | None = None
    genres: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class RemoveCollectionItemCommand:
    """Remove anime item from a collection form payload.

    Attributes:
        collection_id: Target collection identifier.
        anime_id: Anime identifier to remove.
    """

    collection_id: int
    anime_id: int
