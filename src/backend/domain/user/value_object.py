from dataclasses import dataclass

from src.backend.domain.highlight.value_object import (
    HighlightActivityItem,
    HighlightCard,
    HighlightProfileSummary,
)


@dataclass
class ProfileOverview:
    user_id: int
    email: str
    username: str
    avatar_url: str | None
    created_at: str
    summary: HighlightProfileSummary
    recent_highlights: list[HighlightCard]
    popular_highlights: list[HighlightCard]
    liked_highlights: list[HighlightCard]
    saved_highlights: list[HighlightCard]
    recent_activity: list[HighlightActivityItem]


@dataclass
class PendingEmailVerification:
    email: str
    username: str
    password_hash: str
    code: str
    theme: str = "neon"
