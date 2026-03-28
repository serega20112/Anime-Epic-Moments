from __future__ import annotations

from collections import OrderedDict
from threading import RLock
from time import monotonic
from typing import Callable, Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class TTLCache(Generic[K, V]):
    """Небольшой потокобезопасный TTL-кэш в памяти."""

    def __init__(self, ttl_seconds: float, max_entries: int = 512):
        self.ttl_seconds = max(float(ttl_seconds), 0.0)
        self.max_entries = max(int(max_entries), 1)
        self._items: OrderedDict[K, tuple[float, V]] = OrderedDict()
        self._lock = RLock()

    def contains(self, key: K) -> bool:
        with self._lock:
            return self._get_unlocked(key)[0]

    def get(self, key: K, default: V | None = None) -> V | None:
        with self._lock:
            found, value = self._get_unlocked(key)
            return value if found else default

    def set(self, key: K, value: V) -> V:
        expires_at = monotonic() + self.ttl_seconds
        with self._lock:
            self._prune_expired_unlocked()
            self._items[key] = (expires_at, value)
            self._items.move_to_end(key)
            while len(self._items) > self.max_entries:
                self._items.popitem(last=False)
        return value

    def delete(self, key: K):
        with self._lock:
            self._items.pop(key, None)

    def delete_matching(self, predicate: Callable[[K], bool]):
        with self._lock:
            for key in [cache_key for cache_key in self._items.keys() if predicate(cache_key)]:
                self._items.pop(key, None)

    def clear(self):
        with self._lock:
            self._items.clear()

    def _get_unlocked(self, key: K) -> tuple[bool, V | None]:
        item = self._items.get(key)
        if item is None:
            return False, None
        expires_at, value = item
        if expires_at <= monotonic():
            self._items.pop(key, None)
            return False, None
        self._items.move_to_end(key)
        return True, value

    def _prune_expired_unlocked(self):
        now = monotonic()
        expired_keys = [
            key for key, (expires_at, _value) in self._items.items() if expires_at <= now
        ]
        for key in expired_keys:
            self._items.pop(key, None)
