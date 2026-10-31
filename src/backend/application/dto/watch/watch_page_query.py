"""Параметры запроса страницы просмотра аниме."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WatchPageQuery:
    """Параметры сборки страницы просмотра.

    Attributes:
        anime_id: Идентификатор аниме.
        episode: Запрошенный номер серии.
        selected_source_id: Идентификатор ранее выбранного источника.
        preferred_start_seconds: Позиция, с которой нужно продолжить просмотр.
        discussion_sort: Порядок сортировки обсуждения.
        user_id: Идентификатор зрителя либо None для гостя.
    """

    anime_id: int
    episode: int = 1
    selected_source_id: int | None = None
    preferred_start_seconds: float | None = None
    discussion_sort: str = "popular"
    user_id: int | None = None
