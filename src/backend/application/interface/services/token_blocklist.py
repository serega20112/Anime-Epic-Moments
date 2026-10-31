"""Порт списка отозванных токенов."""

from __future__ import annotations

from abc import ABC, abstractmethod


class TokenBlocklistInterface(ABC):
    """Отзыв и проверка одноразовых JWT-токенов."""

    @abstractmethod
    async def revoke(self, token: str, ttl_seconds: int) -> None:
        """Пометить токен отозванным на заданный срок."""

    @abstractmethod
    async def consume(self, token: str, ttl_seconds: int) -> bool:
        """Атомарно отозвать токен, если он ещё не отозван.

        При одновременных запросах True получает только один вызывающий.
        """

    @abstractmethod
    async def is_revoked(self, token: str) -> bool:
        """Проверить, отозван ли токен сейчас."""
