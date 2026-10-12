"""Value object describing a genre discovered inside the current result set."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GenreFacet:
    """A genre that actually occurs in the scanned catalog results.

    Facets are derived from the titles the provider returned instead of a
    static vocabulary, so the filter panel only offers genres the user can
    actually match against the current selection.

    Attributes:
        name: Genre name exactly as the provider reported it.
        count: Number of scanned titles carrying the genre.
    """

    name: str
    count: int

    def to_dict(self) -> dict[str, object]:
        """Convert the facet to a serializable mapping.

        Returns:
            dict[str, object]: Facet name and count.
        """
        return {"name": self.name, "count": self.count}
