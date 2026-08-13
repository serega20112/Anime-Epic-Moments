"""Thread-safe in-memory TTL cache used by application services."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable
from threading import RLock
from time import monotonic
from typing import TypeVar

K = TypeVar("K")
V = TypeVar("V")


class TTLCache[K, V]:
    """A small thread-safe in-memory cache with TTL-based expiration."""

    def __init__(self, ttl_seconds: float, max_entries: int = 512):
        """Initialize the cache.

        Args:
            ttl_seconds: Entry lifetime in seconds.
            max_entries: Maximum number of cached entries.
        """
        self.ttl_seconds = max(float(ttl_seconds), 0.0)
        self.max_entries = max(int(max_entries), 1)
        self._items: OrderedDict[K, tuple[float, V]] = OrderedDict()
        self._lock = RLock()

    def contains(self, key: K) -> bool:
        """Return whether a live entry exists for the key.

        Args:
            key: Cache key.

        Returns:
            bool: True when an unexpired entry exists.
        """
        with self._lock:
            return self._get_unlocked(key)[0]

    def get(self, key: K, default: V | None = None) -> V | None:
        """Return a live entry value or the default.

        Args:
            key: Cache key.
            default: Value returned when no live entry exists.

        Returns:
            V | None: Stored value or the default.
        """
        with self._lock:
            found, value = self._get_unlocked(key)
            return value if found else default

    def set(self, key: K, value: V) -> V:
        """Store an entry, evicting the oldest when at capacity.

        Args:
            key: Cache key.
            value: Value to store.

        Returns:
            V: The stored value.
        """
        expires_at = monotonic() + self.ttl_seconds
        with self._lock:
            self._prune_expired_unlocked()
            self._items[key] = (expires_at, value)
            self._items.move_to_end(key)
            while len(self._items) > self.max_entries:
                self._items.popitem(last=False)
        return value

    def delete(self, key: K) -> None:
        """Remove an entry by key.

        Args:
            key: Cache key.
        """
        with self._lock:
            self._items.pop(key, None)

    def delete_matching(self, predicate: Callable[[K], bool]) -> None:
        """Remove entries whose keys satisfy the predicate.

        Args:
            predicate: Function returning True for keys to delete.
        """
        with self._lock:
            for key in [cache_key for cache_key in self._items.keys() if predicate(cache_key)]:
                self._items.pop(key, None)

    def clear(self) -> None:
        """Remove all entries."""
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

    def _prune_expired_unlocked(self) -> None:
        now = monotonic()
        expired_keys = [
            key for key, (expires_at, _value) in self._items.items() if expires_at <= now
        ]
        for key in expired_keys:
            self._items.pop(key, None)
