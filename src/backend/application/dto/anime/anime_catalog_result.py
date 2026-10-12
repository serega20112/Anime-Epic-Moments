"""Result of browsing the anime catalog as one page with filter facets."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.domain.entities.anime.anime import Anime
from backend.domain.value_objects.anime.genre_facet import GenreFacet


@dataclass(frozen=True, slots=True)
class AnimeCatalogResult:
    """One page of catalog results plus the metadata the UI needs.

    Attributes:
        items: Anime belonging to the requested page.
        page: One-based number of the served page.
        per_page: Page size used to build the slice.
        total: Number of titles available for the current filters.
        total_is_exact: Whether ``total`` is definitive or limited by the
            size of the scanned provider window.
        genre_facets: Genres observed in the scanned results, most frequent
            first.
    """

    items: tuple[Anime, ...] = field(default_factory=tuple)
    page: int = 1
    per_page: int = 25
    total: int = 0
    total_is_exact: bool = True
    genre_facets: tuple[GenreFacet, ...] = field(default_factory=tuple)

    @property
    def total_pages(self) -> int:
        """Number of pages available for the current filters.

        Returns:
            int: Total page count, at least one.
        """
        if self.total <= 0:
            return 1
        return max(1, -(-self.total // self.per_page))

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

    def to_dict(self) -> dict[str, object]:
        """Convert the result into a JSON-serializable mapping.

        Returns:
            dict[str, object]: Payload consumed by the catalog UI.
        """
        return {
            "items": [vars(anime) for anime in self.items],
            "page": self.page,
            "per_page": self.per_page,
            "total": self.total,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_previous": self.has_previous,
            "total_is_exact": self.total_is_exact,
            "genre_facets": [facet.to_dict() for facet in self.genre_facets],
        }
