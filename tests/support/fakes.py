"""Двойники портов, на которых проверяются сценарии."""

from __future__ import annotations

from typing import Any

from backend.application.interface.unit_of_work import UnitOfWorkInterface


class FakeUnitOfWork(UnitOfWorkInterface):
    """Единица работы, отдающая заранее заготовленные двойники репозиториев.

    Репозитории передаются по имени класса порта, поэтому тест описывает только
    те порты, которые сценарий действительно запрашивает.
    """

    def __init__(self, **repositories: Any) -> None:
        """Создать двойник с репозиториями по именам портов.

        Args:
            **repositories: Двойники репозиториев, ключ — имя класса порта.
        """
        super().__init__()
        self._repositories = repositories
        self.commits = 0
        self.rollbacks = 0

    def repository(self, repository_type):
        """Вернуть двойник репозитория по имени порта.

        Args:
            repository_type: Порт репозитория из слоя application.

        Returns:
            Двойник, переданный в конструктор.

        Raises:
            LookupError: Если тест не подготовил репозиторий для этого порта.
        """
        try:
            return self._repositories[repository_type.__name__]
        except KeyError as error:
            raise LookupError(
                f"Тест не подготовил двойник для порта {repository_type.__name__}"
            ) from error

    async def commit(self) -> None:
        """Зафиксировать транзакцию в двойнике, только считая вызовы."""
        self.commits += 1

    async def rollback(self) -> None:
        """Отменить транзакцию в двойнике, только считая вызовы."""
        self.rollbacks += 1
