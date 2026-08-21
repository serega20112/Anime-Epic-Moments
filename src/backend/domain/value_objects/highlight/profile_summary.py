from dataclasses import dataclass


@dataclass
class HighlightProfileSummary:
    highlight_count: int
    like_count: int
    saved_count: int


@dataclass
class HighlightActivityItem:
    action: str
    actor_user_id: int
    actor_username: str
    highlight_id: int
    highlight_title: str
    created_at: str
