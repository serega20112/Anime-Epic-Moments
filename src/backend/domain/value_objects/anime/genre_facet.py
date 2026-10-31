"""Значимый объект жанра, найденного в текущей выдаче."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GenreFacet:
    """Жанр, реально встречающийся в просмотренных результатах каталога."""

    name: str
    count: int
