"""Create collection form payload."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateCollectionCommand:
    """Create collection form payload.

    Attributes:
        user_id: Owner user identifier.
        title: Collection title.
        description: Optional collection description.
        cover_url: Optional public URL of the collection cover image.
        is_public: Whether the collection is publicly visible.
    """

    user_id: int
    title: str
    description: str = ""
    is_public: bool = True
    cover_url: str | None = None
