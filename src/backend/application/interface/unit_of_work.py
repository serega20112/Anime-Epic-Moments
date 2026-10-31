"""Порт границы транзакции для слоя application."""

from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import TypeVar

T = TypeVar("T")


class UnitOfWorkInterface(ABC):
    """Граница единицы работы: выдаёт репозитории и фиксирует изменения.

    Конкретный адаптер владеет транзакцией (например, сессией базы).
    Сценарии входят в контекст, берут репозитории через :meth:`repository`
    и не управляют транзакцией напрямую.
    """

    def __init__(self) -> None:
        """Создать границу единицы работы с нулевой вложенностью."""
        self._depth = 0

    @abstractmethod
    def repository(self, repository_type: type[T]) -> T:
        """Вернуть репозиторий, работающий в этой транзакции.

        Args:
            repository_type: Порт репозитория, объявленный в application.

        Returns:
            Экземпляр репозитория, привязанный к текущей транзакции.
        """

    @abstractmethod
    async def commit(self) -> None:
        """Зафиксировать все накопленные изменения атомарно."""

    @abstractmethod
    async def rollback(self) -> None:
        """Отменить все накопленные изменения."""

    async def __aenter__(self) -> UnitOfWorkInterface:
        """Войти в контекст единицы работы."""
        self._depth += 1
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Зафиксировать при успехе и откатить при ошибке внешнего уровня."""
        self._depth = max(self._depth - 1, 0)
        if self._depth > 0:
            return False
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()
        return False
