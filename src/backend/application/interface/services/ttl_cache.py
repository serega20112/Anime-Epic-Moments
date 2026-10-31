"""Порт кэша с ограниченным временем жизни значений.

Приложение обращается к кэшу только через этот абстрактный класс, а реализация
живёт в инфраструктуре. Порт описывает то, что действительно нужно
потребителям: чтение, запись с необязательным TTL, проверка наличия, удаление
по ключу и по предикату, полная очистка и освобождение ресурсов.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class TTLCacheInterface(ABC):
    """Кэш «ключ -> значение» с истечением по времени."""

    @abstractmethod
    async def get(self, key: Any, default: Any = None) -> Any:
        """Вернуть значение по ключу либо значение по умолчанию.

        Args:
            key: Ключ кэша.
            default: Значение для отсутствующего или истёкшего ключа.

        Returns:
            Any: Сохранённое значение либо default.
        """

    @abstractmethod
    async def set(self, key: Any, value: Any, ttl_seconds: int | None = None) -> None:
        """Сохранить значение с необязательным собственным TTL.

        Args:
            key: Ключ кэша.
            value: Сохраняемое значение.
            ttl_seconds: Собственный TTL в секундах; None — общий для кэша.
        """

    @abstractmethod
    async def contains(self, key: Any) -> bool:
        """Проверить, есть ли живое значение по ключу.

        Args:
            key: Ключ кэша.

        Returns:
            bool: True для неистёкшей записи.
        """

    @abstractmethod
    async def delete(self, key: Any) -> None:
        """Удалить значение по ключу.

        Args:
            key: Ключ кэша.
        """

    @abstractmethod
    async def delete_matching(self, predicate: Callable[[Any], bool]) -> None:
        """Удалить записи, ключи которых удовлетворяют предикату.

        Args:
            predicate: Функция, возвращающая True удаляемым ключам.
        """

    @abstractmethod
    async def clear(self) -> None:
        """Удалить все записи кэша."""

    @abstractmethod
    async def close(self) -> None:
        """Освободить ресурсы кэша."""
