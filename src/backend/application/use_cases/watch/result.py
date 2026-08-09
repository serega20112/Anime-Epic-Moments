"""Result types returned by watch use cases.

Use cases return a :class:`WatchResult` instead of raising domain errors so the
presentation layer stays free of error-handling logic and only reads the
outcome fields to build the JSON response.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class WatchResult:
    """Outcome of a watch use case.

    Attributes:
        ok: Whether the operation succeeded.
        status_code: HTTP status to return.
        data: Optional payload produced on success.
        error: Error code/message returned on failure.
    """

    ok: bool
    status_code: int = 200
    data: Any = None
    error: str | None = None

    @classmethod
    def success(cls, data: Any = None, status_code: int = 200) -> WatchResult:
        """Build a successful result.

        Args:
            data: Optional payload.
            status_code: HTTP status for the response.

        Returns:
            WatchResult: Successful result.
        """
        return cls(ok=True, status_code=status_code, data=data)

    @classmethod
    def failure(cls, error: str, status_code: int = 400) -> WatchResult:
        """Build a failed result.

        Args:
            error: Error code/message for the response.
            status_code: HTTP status for the response.

        Returns:
            WatchResult: Failed result.
        """
        return cls(ok=False, status_code=status_code, error=error)