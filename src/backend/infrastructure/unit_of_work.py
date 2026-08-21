"""SQLAlchemy unit of work adapter."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.interface.unit_of_work import UnitOfWorkInterface


class SqlAlchemyUnitOfWork(UnitOfWorkInterface):
    """Unit of work backed by a shared async database session.

    Repositories flush pending changes into the current transaction; this
    adapter demarcates and persists that transaction on behalf of a use case.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def commit(self) -> None:
        """Persist all pending changes atomically.

        Raises:
            Exception: When the database rejects the transaction.
        """
        await self._session.commit()

    async def rollback(self) -> None:
        """Discard all pending changes."""
        await self._session.rollback()
