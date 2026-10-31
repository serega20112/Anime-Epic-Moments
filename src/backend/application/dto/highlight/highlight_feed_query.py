"""Параметры фильтрации социальной ленты хайлайтов."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HighlightFeedQuery:
    """Параметры фильтрации общей ленты хайлайтов.

    Attributes:
        anime_id: Фильтр по аниме.
        category: Фильтр по категории.
        include_spoilers: Показывать ли спойлеры.
        limit: Максимальное число записей.
        viewer_user_id: Идентификатор зрителя для отметок лайков и сохранений.
    """

    anime_id: int | None = None
    category: str | None = None
    include_spoilers: bool = False
    limit: int = 12
    viewer_user_id: int | None = None
