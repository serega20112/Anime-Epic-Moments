"""Transaction boundary abstraction for the application layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType


class UnitOfWorkInterface(ABC):
    """Boundary that demarcates and persists a unit of work.

    Concrete adapters own the underlying transaction (for example a database
    session). Use cases rely on this abstraction so transaction handling stays
    in the application layer instead of leaking into repositories.
    """

    @abstractmethod
    async def commit(self) -> None:
        """Persist all pending changes atomically."""

    @abstractmethod
    async def rollback(self) -> None:
        """Discard all pending changes."""

    async def __aenter__(self) -> UnitOfWorkInterface:
        """Enter the unit of work context.

        Returns:
            UnitOfWorkInterface: Self for use in ``async with``.
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Commit on success and roll back on failure.

        Args:
            exc_type: Raised exception type or None.
            exc_val: Raised exception value or None.
            exc_tb: Raised exception traceback or None.

        Returns:
            bool: False so exceptions propagate.
        """
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()
        return False
