"""Параметры запроса поиска аниме по названию."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SearchAnimeQuery:
    """Параметры поиска аниме по названию.

    Attributes:
        title: Искомое название.
        limit: Максимальное число результатов.
        include_adult: Учитывать ли взрослый контент.
    """

    title: str
    limit: int = 10
    include_adult: bool = False
