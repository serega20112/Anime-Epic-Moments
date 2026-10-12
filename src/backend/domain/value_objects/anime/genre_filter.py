"""Value object describing a catalog genre selection with configurable semantics."""

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
    """How a multi-genre selection is combined when matching a title.

    Attributes:
        ANY: A title passes when it carries at least one selected genre.
        ALL: A title passes only when it carries every selected genre.
    """

    ANY = "any"
    ALL = "all"

    @classmethod
    def parse(cls, value: object) -> GenreMatchMode:
        """Parse a raw request value into a match mode.

        Args:
            value: Raw value, usually a query parameter.

        Returns:
            GenreMatchMode: Parsed mode, defaulting to ALL for unknown input.
        """
        text = str(value or "").strip().lower()
        if text in {"any", "or", "любое", "хотя бы одно"}:
            return cls.ANY
        return cls.ALL


def normalize_genre(value: str | None) -> str:
    """Normalize a genre name to a comparable lowercase form.

    Args:
        value: Raw genre name coming from a request or a provider payload.

    Returns:
        str: Lowercased name with punctuation collapsed to single spaces.
    """
    text = _NON_ALNUM_RE.sub(" ", str(value or "").strip().lower())
    collapsed = " ".join(text.split())
    return _ALIASES.get(collapsed, collapsed)


@dataclass(frozen=True, slots=True)
class GenreFilter:
    """Immutable set of genres used to decide whether a title passes.

    The selection is conjunctive by default: a title matches only when it
    carries every selected genre, which mirrors the reading of "a romantic
    comedy". Switching the mode to :attr:`GenreMatchMode.ANY` relaxes the
    selection to a disjunction, where carrying a single genre is enough.

    Attributes:
        terms: Normalized genre names that take part in the match.
        mode: Strategy used to combine several terms.
    """

    terms: frozenset[str] = frozenset()
    mode: GenreMatchMode = GenreMatchMode.ALL

    @classmethod
    def from_values(
        cls,
        values: Iterable[str] | None,
        mode: GenreMatchMode = GenreMatchMode.ALL,
    ) -> GenreFilter:
        """Build a filter from raw genre names.

        Args:
            values: Raw genre names; empty or missing values are ignored.
            mode: Strategy used to combine several names.

        Returns:
            GenreFilter: Filter holding every non-empty normalized term.
        """
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
        """Check whether a title satisfies the selected genres.

        Args:
            genres: Genre names reported by the catalog provider.
            tags: Tag names reported by the catalog provider.

        Returns:
            bool: True when the filter is empty, or when the provider genres
                satisfy the configured match mode.
        """
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
        """Report whether the filter narrows the catalog at all.

        Returns:
            bool: True when at least one genre is selected.
        """
        return bool(self.terms)
