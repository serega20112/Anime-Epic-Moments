"""Значимый объект выбора жанров каталога с настраиваемой семантикой."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

_NON_ALNUM_RE = re.compile(r"[^a-z0-9а-яё]+")

_ALIASES: dict[str, str] = {
    "science fiction": "sci fi",
    "sci-fi": "sci fi",
    "slice of life": "slice of life",
    "mahou shoujo": "magic shoujo",
    "shoujo": "magic shoujo",
    "seinen": "seinen",
    "shounen": "shounen",
    "josei": "josei",
    "kids": "kids",
    "martial arts": "martial arts",
    "super power": "super power",
}


class GenreMatchMode(StrEnum):
    """Способ объединения нескольких выбранных жанров при отборе."""

    ANY = "any"
    ALL = "all"

    @classmethod
    def parse(cls, value: object) -> GenreMatchMode:
        """Разобрать сырое значение запроса в режим совпадения."""
        text = str(value or "").strip().lower()
        if text in {"any", "or", "любое", "хотя бы одно"}:
            return cls.ANY
        return cls.ALL


def normalize_genre(value: str | None) -> str:
    """Привести название жанра к сравнимому виду."""
    text = _NON_ALNUM_RE.sub(" ", str(value or "").strip().lower())
    collapsed = " ".join(text.split())
    return _ALIASES.get(collapsed, collapsed)


@dataclass(frozen=True, slots=True)
class GenreFilter:
    """Неизменяемый набор жанров для проверки прохождения тайтла."""

    terms: frozenset[str] = frozenset()
    mode: GenreMatchMode = GenreMatchMode.ALL

    @classmethod
    def from_values(
        cls,
        values: Iterable[str] | None,
        mode: GenreMatchMode = GenreMatchMode.ALL,
    ) -> GenreFilter:
        """Собрать фильтр из сырых названий жанров."""
        terms = {
            normalized
            for normalized in (normalize_genre(value) for value in values or ())
            if normalized
        }
        return cls(frozenset(terms), mode)

    def matches(
        self,
        genres: Iterable[str] | None,
        tags: Iterable[str] | None = None,
    ) -> bool:
        """Проверить, проходит ли тайтл по выбранным жанрам."""
        if not self.terms:
            return True
        available = {
            normalized
            for normalized in (normalize_genre(value) for value in (*(genres or ()), *(tags or ())))
            if normalized
        }
        if self.mode is GenreMatchMode.ANY:
            return bool(self.terms & available)
        return self.terms <= available

    def __bool__(self) -> bool:
        """Сообщить, сужает ли фильтр выдачу каталога."""
        return bool(self.terms)
