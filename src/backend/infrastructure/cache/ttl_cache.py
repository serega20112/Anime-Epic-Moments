"""Asyncio-безопасный in-memory кэш с истечением по времени.

Единственная реализация порта :class:`TTLCacheInterface` в проекте. Нужна там,
где значение дорого доставать извне (внешние провайдеры озвучек), но держать
его вечно нельзя. Хранение — ``OrderedDict`` с вытеснением самых старых записей
при переполнении; все операции под ``asyncio.Lock``, поэтому параллельные
запросы одного процесса не видят полузаписанных состояний.
"""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from collections.abc import Callable
from time import monotonic

from backend.application.interface.services.ttl_cache import TTLCacheInterface


class TTLCache[K, V](TTLCacheInterface):
    """Небольшой asyncio-безопасный кэш с истечением записей по времени."""

    def __init__(self, ttl_seconds: float, max_entries: int = 512) -> None:
        """Создать кэш.

        Args:
            ttl_seconds: Время жизни записи в секундах.
            max_entries: Максимальное число хранимых записей.
        """
        self.ttl_seconds = max(float(ttl_seconds), 0.0)
        self.max_entries = max(int(max_entries), 1)
        self._items: OrderedDict[K, tuple[float, V]] = OrderedDict()
        self._lock = asyncio.Lock()

    async def contains(self, key: K) -> bool:
        """Вернуть, есть ли живая запись по ключу.

        Args:
            key: Ключ кэша.

        Returns:
            bool: True для неистёкшей записи.
        """
        async with self._lock:
            found, _value = await self._get_unlocked(key)
            return found

    async def get(self, key: K, default: V | None = None) -> V | None:
        """Вернуть значение живой записи либо значение по умолчанию.

        Args:
            key: Ключ кэша.
            default: Значение для отсутствующей или истёкшей записи.

        Returns:
            V | None: Сохранённое значение либо default.
        """
        async with self._lock:
            found, value = await self._get_unlocked(key)
            return value if found else default

    async def set(self, key: K, value: V, ttl_seconds: int | None = None) -> None:
        """Сохранить запись, вытесняя самые старые при переполнении.

        Args:
            key: Ключ кэша.
            value: Сохраняемое значение.
            ttl_seconds: Собственный TTL записи; None использует общий TTL кэша.
        """
        lifetime = float(ttl_seconds) if ttl_seconds is not None else self.ttl_seconds
        expires_at = monotonic() + lifetime
        async with self._lock:
            await self._prune_expired_unlocked()
            self._items[key] = (expires_at, value)
            self._items.move_to_end(key)
            while len(self._items) > self.max_entries:
                self._items.popitem(last=False)

    async def delete(self, key: K) -> None:
        """Удалить запись по ключу.

        Args:
            key: Ключ кэша.
        """
        async with self._lock:
            self._items.pop(key, None)

    async def delete_matching(self, predicate: Callable[[K], bool]) -> None:
        """Удалить записи, ключи которых удовлетворяют предикату.

        Args:
            predicate: Функция, возвращающая True удаляемым ключам.
        """
        async with self._lock:
            for cache_key in [item_key for item_key in self._items.keys() if predicate(item_key)]:
                self._items.pop(cache_key, None)

    async def clear(self) -> None:
        """Удалить все записи кэша."""
        async with self._lock:
            self._items.clear()

    async def close(self) -> None:
        """Освободить ресурсы: in-memory кэш внешних соединений не имеет.

        Exists to satisfy the port contract so consumers can release caches
        uniformly, including Redis-backed implementations.
        """
        await self.clear()

    async def _get_unlocked(self, key: K) -> tuple[bool, V | None]:
        """Прочитать запись без захвата блокировки.

        Args:
            key: Ключ кэша.

        Returns:
            tuple[bool, V | None]: Признак нахождения и значение.
        """
        item = self._items.get(key)
        if item is None:
            return False, None
        expires_at, value = item
        if expires_at <= monotonic():
            self._items.pop(key, None)
            return False, None
        self._items.move_to_end(key)
        return True, value

    async def _prune_expired_unlocked(self) -> None:
        """Сбросить просроченные записи без захвата блокировки."""
        now = monotonic()
        expired_keys = [
            key for key, (expires_at, _value) in self._items.items() if expires_at <= now
        ]
        for key in expired_keys:
            self._items.pop(key, None)
