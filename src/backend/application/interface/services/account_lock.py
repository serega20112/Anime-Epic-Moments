"""Порт блокировки аккаунта после неудачных попыток входа."""

from __future__ import annotations

from abc import ABC, abstractmethod


class AccountLockServiceInterface(ABC):
    """Учёт неудачных попыток входа и состояние блокировки аккаунта."""

    @abstractmethod
    async def is_account_locked(self, email: str) -> tuple[bool, str | None]:
        """Проверить, заблокирован ли аккаунт сейчас.

        Returns:
            tuple[bool, str | None]: Признак блокировки и момент разблокировки.
        """

    @abstractmethod
    async def record_failed_attempt(self, email: str) -> object:
        """Учесть неудачную попытку входа и заблокировать аккаунт при перерасходе.

        Возвращаемое состояние здесь не разбирается: сценарию входа важен сам
        факт учёта попытки.
        """

    @abstractmethod
    async def unlock_account(self, email: str) -> bool:
        """Снять блокировку после успешного входа."""
