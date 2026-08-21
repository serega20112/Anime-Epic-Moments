"""Ask AI recommendations payload."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AskAiRecommendationsCommand:
    """Ask AI recommendations payload.

    Attributes:
        user_id: User identifier.
        query: Free-form recommendation request text.
        limit: Maximum number of recommendations to return.
    """

    user_id: int
    query: str
    limit: int = 6
