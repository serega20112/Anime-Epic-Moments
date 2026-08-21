"""Result types returned by reaction use cases."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from starlette import status


@dataclass
class ReactionResult:
    """Outcome of a reaction use case.

    Attributes:
        ok: Whether the operation succeeded.
        status_code: HTTP status to return.
        data: Optional payload produced on success.
        error: Error code/message returned on failure.
    """

    ok: bool
    status_code: int = status.HTTP_200_OK
    data: Any = None
    error: str | None = None

    @classmethod
    async def success(
        cls, data: Any = None, status_code: int = status.HTTP_200_OK
    ) -> ReactionResult:
        """Build a successful result.

        Args:
            data: Optional payload.
            status_code: HTTP status for the response.

        Returns:
            ReactionResult: Successful result.
        """
        return cls(ok=True, status_code=status_code, data=data)

    @classmethod
    async def failure(
        cls, error: str, status_code: int = status.HTTP_400_BAD_REQUEST
    ) -> ReactionResult:
        """Build a failed result.

        Args:
            error: Error code/message for the response.
            status_code: HTTP status for the response.

        Returns:
            ReactionResult: Failed result.
        """
        return cls(ok=False, status_code=status_code, error=error)
