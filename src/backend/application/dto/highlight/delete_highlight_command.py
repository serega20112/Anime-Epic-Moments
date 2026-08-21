"""Delete highlight payload."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeleteHighlightCommand:
    """Delete highlight payload.

    Attributes:
        highlight_id: Highlight identifier.
    """

    highlight_id: int
