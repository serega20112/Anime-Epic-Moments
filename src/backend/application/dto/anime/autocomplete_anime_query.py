"""Параметры запроса автодополнения названий аниме."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AutocompleteAnimeQuery:
    """Параметры запроса автодополнения названий аниме.

    Attributes:
        query: Частично введённое название.
        limit: Максимальное число подсказок.
        include_adult: Учитывать ли взрослый контент.
    """

    query: str
    limit: int = 5
    include_adult: bool = False
