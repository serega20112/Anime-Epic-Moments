"""Publish a draft viewing moment as a highlight."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PublishViewingMomentCommand:
    """Publish a draft viewing moment as a highlight.

    Attributes:
        user_id: Owner user identifier.
        moment_id: Moment identifier to publish.
        is_spoiler: Whether the highlight contains spoilers.
        title: Optional title override.
        category: Optional category override.
        emotion: Optional emotion label.
        description: Optional description.
    """

    user_id: int
    moment_id: int
    is_spoiler: bool = False
    title: str | None = None
    category: str | None = None
    emotion: str | None = None
    description: str | None = None
