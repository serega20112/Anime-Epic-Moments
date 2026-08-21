"""Порты приложения: интерфейсы репозиториев, сервисов и границы транзакции.

Реализации живут в infrastructure; use cases и DI зависят только от этих контрактов.
"""

from backend.application.interface.unit_of_work import UnitOfWorkInterface

__all__ = ["UnitOfWorkInterface"]
