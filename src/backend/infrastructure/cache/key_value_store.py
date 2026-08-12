from __future__ import annotations

import pickle
from threading import RLock
from time import monotonic
from typing import Any


class KeyValueStore:
    """Store arbitrary values in Redis or an in-memory fallback with TTL support."""

    def __init__(
        self,
        redis_url: str | None = None,
        namespace: str = "anime_epic_moments",
        required: bool = False,
    ):
        """Initialize the store.

        Args:
            redis_url: Optional Redis connection URL.
            namespace: Key namespace prefix.
            required: Whether Redis is mandatory when a URL is given.
        """
        self.namespace = str(namespace or "anime_epic_moments").strip(":")
        self._redis = self._build_redis(redis_url=redis_url, required=required)
        self._items: dict[str, tuple[float | None, Any]] = {}
        self._lock = RLock()

    @property
    def uses_redis(self) -> bool:
        """Whether the store is backed by Redis."""
        return self._redis is not None

    def _build_redis(self, redis_url: str | None, required: bool):
        if not redis_url:
            return None
        try:
            from redis.asyncio import Redis

            return Redis.from_url(
                redis_url,
                decode_responses=False,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
        except Exception:
            if required:
                raise
            return None

    def _normalize_key(self, key: str) -> str:
        normalized = str(key or "").strip()
        return f"{self.namespace}:{normalized}" if self.namespace else normalized

    def _normalize_ttl(self, ttl_seconds: float | int | None) -> int | None:
        if ttl_seconds is None:
            return None
        return max(int(ttl_seconds), 0)

    def _get_memory_item(self, key: str) -> tuple[bool, Any]:
        self._prune_memory()
        item = self._items.get(key)
        if item is None:
            return False, None
        expires_at, value = item
        if expires_at is not None and expires_at <= monotonic():
            self._items.pop(key, None)
            return False, None
        return True, value

    def _prune_memory(self):
        now = monotonic()
        expired_keys = [
            key
            for key, (expires_at, _value) in self._items.items()
            if expires_at is not None and expires_at <= now
        ]
        for key in expired_keys:
            self._items.pop(key, None)

    async def contains(self, key: str) -> bool:
        """Check whether a key exists.

        Args:
            key: Key to check.

        Returns:
            bool: True when the key exists.
        """
        normalized_key = self._normalize_key(key)
        if self._redis is not None:
            return bool(await self._redis.exists(normalized_key))

        with self._lock:
            found, _value = self._get_memory_item(normalized_key)
            return found

    async def get(self, key: str, default: Any = None) -> Any:
        """Read a value by key.

        Args:
            key: Key to read.
            default: Value returned when the key is missing.

        Returns:
            Any: Stored value or default.
        """
        normalized_key = self._normalize_key(key)
        if self._redis is not None:
            raw_value = await self._redis.get(normalized_key)
            if raw_value is None:
                return default
            return pickle.loads(raw_value)

        with self._lock:
            found, value = self._get_memory_item(normalized_key)
            return value if found else default

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: float | int | None = None,
    ) -> Any:
        """Store a value by key.

        Args:
            key: Key to write.
            value: Value to store.
            ttl_seconds: Optional TTL in seconds.

        Returns:
            Any: The stored value.
        """
        normalized_key = self._normalize_key(key)
        ttl_value = self._normalize_ttl(ttl_seconds)
        if ttl_value == 0:
            await self.delete(key)
            return value

        if self._redis is not None:
            payload = pickle.dumps(value)
            if ttl_value is None:
                await self._redis.set(normalized_key, payload)
            else:
                await self._redis.setex(normalized_key, ttl_value, payload)
            return value

        expires_at = None if ttl_value is None else monotonic() + ttl_value
        with self._lock:
            self._prune_memory()
            self._items[normalized_key] = (expires_at, value)
        return value

    async def consume(
        self,
        key: str,
        ttl_seconds: float | int | None = None,
    ) -> bool:
        """Atomically claim a key, succeeding only if it is not already present.

        Redis uses SET NX; the memory fallback holds the store lock so a key
        can be claimed exactly once across concurrent consumers.

        Args:
            key: Key to claim.
            ttl_seconds: TTL for the claimed entry.

        Returns:
            bool: True if the key was claimed, False if it already existed.
        """
        normalized_key = self._normalize_key(key)
        ttl_value = self._normalize_ttl(ttl_seconds)
        if ttl_value == 0:
            return False

        if self._redis is not None:
            payload = pickle.dumps(True)
            if ttl_value is None:
                claimed = await self._redis.set(normalized_key, payload, nx=True)
            else:
                claimed = await self._redis.set(normalized_key, payload, nx=True, ex=ttl_value)
            return bool(claimed)

        expires_at = None if ttl_value is None else monotonic() + ttl_value
        with self._lock:
            self._prune_memory()
            if normalized_key in self._items:
                return False
            self._items[normalized_key] = (expires_at, True)
        return True

    async def delete(self, key: str):
        """Remove a key.

        Args:
            key: Key to remove.
        """
        normalized_key = self._normalize_key(key)
        if self._redis is not None:
            await self._redis.delete(normalized_key)
            return

        with self._lock:
            self._items.pop(normalized_key, None)

    async def delete_prefix(self, prefix: str):
        """Remove all keys sharing a prefix.

        Args:
            prefix: Key prefix to remove.
        """
        normalized_prefix = self._normalize_key(prefix)
        if self._redis is not None:
            keys = [key async for key in self._redis.scan_iter(f"{normalized_prefix}*")]
            if keys:
                await self._redis.delete(*keys)
            return

        with self._lock:
            self._prune_memory()
            for key in [
                item_key
                for item_key in self._items.keys()
                if item_key.startswith(normalized_prefix)
            ]:
                self._items.pop(key, None)

    async def increment(
        self,
        key: str,
        ttl_seconds: float | int,
        amount: int = 1,
    ) -> int:
        """Atomically increment a counter with a TTL.

        Args:
            key: Counter key.
            ttl_seconds: TTL in seconds.
            amount: Increment amount.

        Returns:
            int: The new counter value.
        """
        normalized_key = self._normalize_key(key)
        ttl_value = max(int(ttl_seconds), 1)
        if self._redis is not None:
            value = int(await self._redis.incrby(normalized_key, int(amount)))
            if await self._redis.ttl(normalized_key) < 0:
                await self._redis.expire(normalized_key, ttl_value)
            return value

        with self._lock:
            found, current_value = self._get_memory_item(normalized_key)
            next_value = int(current_value or 0) + int(amount)
            self._items[normalized_key] = (
                monotonic() + ttl_value,
                next_value if found else next_value,
            )
            return next_value

    async def get_ttl(self, key: str) -> int:
        """Return the remaining TTL of a key.

        Args:
            key: Key to inspect.

        Returns:
            int: Remaining TTL in seconds.
        """
        normalized_key = self._normalize_key(key)
        if self._redis is not None:
            ttl_value = int(await self._redis.ttl(normalized_key))
            return max(ttl_value, 0)

        with self._lock:
            found, _value = self._get_memory_item(normalized_key)
            if not found:
                return 0
            expires_at = self._items.get(normalized_key, (None, None))[0]
            if expires_at is None:
                return 0
            return max(int(expires_at - monotonic()), 0)

    async def clear(self):
        """Remove all stored keys."""
        if self._redis is not None:
            await self.delete_prefix("")
            return

        with self._lock:
            self._items.clear()

    async def close(self):
        """Close the underlying Redis client."""
        if self._redis is not None:
            close = getattr(self._redis, "aclose", None) or getattr(self._redis, "close", None)
            if close is not None:
                result = close()
                if result is not None:
                    await result
