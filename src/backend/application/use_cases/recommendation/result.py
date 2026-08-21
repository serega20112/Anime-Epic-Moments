"""Result types returned by recommendation use cases.

Use cases return a :class:`RecommendationUseCaseResult` instead of raising or
returning bare lists so the presentation layer stays free of error-handling
logic and only reads the outcome fields to build the JSON response.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from starlette import status


@dataclass
class RecommendationUseCaseResult:
    """Outcome of a recommendation use case.

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
    ) -> RecommendationUseCaseResult:
        """Build a successful result.

        Args:
            data: Optional payload.
            status_code: HTTP status for the response.

        Returns:
            RecommendationUseCaseResult: Successful result.
        """
        return cls(ok=True, status_code=status_code, data=data)

    @classmethod
    async def failure(
        cls, error: str, status_code: int = status.HTTP_400_BAD_REQUEST
    ) -> RecommendationUseCaseResult:
        """Build a failed result.

        Args:
            error: Error code/message for the response.
            status_code: HTTP status for the response.

        Returns:
            RecommendationUseCaseResult: Failed result.
        """
        return cls(ok=False, status_code=status_code, error=error)
