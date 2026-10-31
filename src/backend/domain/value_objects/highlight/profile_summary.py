"""Сводка хайлайтов в профиле пользователя."""

from dataclasses import dataclass


@dataclass(frozen=True)
class HighlightProfileSummary:
    """Агрегаты хайлайтов для блока профиля."""

    highlight_count: int
    like_count: int
    saved_count: int


@dataclass(frozen=True)
class HighlightActivityItem:
    """Событие активности пользователя по хайлайтам."""

    action: str
    actor_user_id: int
    actor_username: str
    highlight_id: int
    highlight_title: str
    created_at: str
