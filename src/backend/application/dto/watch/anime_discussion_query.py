"""Параметры чтения обсуждения аниме."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AnimeDiscussionQuery:
    """Запрос доски обсуждения аниме.

    Attributes:
        anime_id: Идентификатор аниме.
        sort_by: Критерий сортировки ('popular' или 'recent').
        viewer_user_id: Идентификатор зрителя для отметки «лайкнуто».
        limit: Максимальное число комментариев.
    """

    anime_id: int
    sort_by: str = "popular"
    viewer_user_id: int | None = None
    limit: int = 20
