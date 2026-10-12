"""Value object carrying one page of catalog results with pagination metadata."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from backend.domain.entities.anime.anime import Anime


@dataclass(frozen=True, slots=True)
class CatalogPage:
    """A slice of catalog results together with the pagination state.

    Attributes:
        items: Anime belonging to the requested page.
        page: One-based page number that was served.
        per_page: Page size used to compute the slice.
        total: Number of items known to be available in the catalog window.
        total_is_exact: Whether ``total`` is the definitive catalog size
            rather than the size of the scanned window.
    """

    items: tuple[Anime, ...]
    page: int
    per_page: int
    total: int
    total_is_exact: bool = True

    @classmethod
    def build(
        cls,
        items: Sequence[Anime],
        *,
        page: int,
        per_page: int,
        total: int,
        total_is_exact: bool = True,
    ) -> CatalogPage:
        """Create a page, normalizing the page number and total.

        Args:
            items: Anime belonging to the requested page.
            page: One-based page number.
            per_page: Page size.
            total: Number of available items.
            total_is_exact: Whether the total is definitive.

        Returns:
            CatalogPage: Normalized page value object.
        """
        return cls(
            items=tuple(items),
            page=max(1, int(page)),
            per_page=max(1, int(per_page)),
            total=max(0, int(total)),
            total_is_exact=total_is_exact,
        )

    @property
    def total_pages(self) -> int:
        """Number of pages the catalog can be split into.

        Returns:
            int: Total page count, at least one.
        """
        if self.total <= 0:
            return 1
        return max(1, math.ceil(self.total / self.per_page))

    @property
    def has_next(self) -> bool:
        """Whether a page after the current one exists.

        Returns:
            bool: True when the current page is not the last one.
        """
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """Whether a page before the current one exists.

        Returns:
            bool: True when the current page is not the first one.
        """
        return self.page > 1

    def __len__(self) -> int:
        """Return the number of items on the page.

        Returns:
            int: Item count of the current page.
        """
        return len(self.items)
