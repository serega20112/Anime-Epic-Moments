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
        self.namespace = str(namespace or "anime_epic_moments").strip(":")
        self._redis_async = self._build_async_redis(redis_url=redis_url, required=required)
        self._redis_sync = self._build_sync_redis(redis_url=redis_url, required=required)
        self._items: dict[str, tuple[float | None, Any]] = {}
        self._lock = RLock()

    @property
    def uses_redis(self) -> bool:
        return self._redis_async is not None or self._redis_sync is not None

    async def contains(self, key: str) -> bool:
        normalized_key = self._normalize_key(key)
        if self._redis_async is not None:
            return bool(await self._redis_async.exists(normalized_key))

        with self._lock:
            found, _value = self._get_memory_item(normalized_key)
            return found

    def contains_sync(self, key: str) -> bool:
        normalized_key = self._normalize_key(key)
        if self._redis_sync is not None:
            return bool(self._redis_sync.exists(normalized_key))

        with self._lock:
            found, _value = self._get_memory_item(normalized_key)
            return found

    async def get(self, key: str, default: Any = None) -> Any:
        normalized_key = self._normalize_key(key)
        if self._redis_async is not None:
            raw_value = await self._redis_async.get(normalized_key)
            if raw_value is None:
                return default
            return pickle.loads(raw_value)

        with self._lock:
            found, value = self._get_memory_item(normalized_key)
            return value if found else default

    def get_sync(self, key: str, default: Any = None) -> Any:
        normalized_key = self._normalize_key(key)
        if self._redis_sync is not None:
            raw_value = self._redis_sync.get(normalized_key)
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
        normalized_key = self._normalize_key(key)
        ttl_value = self._normalize_ttl(ttl_seconds)
        if ttl_value == 0:
            await self.delete(key)
            return value

        if self._redis_async is not None:
            payload = pickle.dumps(value)
            if ttl_value is None:
                await self._redis_async.set(normalized_key, payload)
            else:
                await self._redis_async.setex(normalized_key, ttl_value, payload)
            return value

        expires_at = None if ttl_value is None else monotonic() + ttl_value
        with self._lock:
            self._prune_memory()
            self._items[normalized_key] = (expires_at, value)
        return value

    def set_sync(
        self,
        key: str,
        value: Any,
        ttl_seconds: float | int | None = None,
    ) -> Any:
        normalized_key = self._normalize_key(key)
        ttl_value = self._normalize_ttl(ttl_seconds)
        if ttl_value == 0:
            self.delete_sync(key)
            return value

        if self._redis_sync is not None:
            payload = pickle.dumps(value)
            if ttl_value is None:
                self._redis_sync.set(normalized_key, payload)
            else:
                self._redis_sync.setex(normalized_key, ttl_value, payload)
            return value

        expires_at = None if ttl_value is None else monotonic() + ttl_value
        with self._lock:
            self._prune_memory()
            self._items[normalized_key] = (expires_at, value)
        return value

    async def delete(self, key: str):
        normalized_key = self._normalize_key(key)
        if self._redis_async is not None:
            await self._redis_async.delete(normalized_key)
            return

        with self._lock:
            self._items.pop(normalized_key, None)

    def delete_sync(self, key: str):
        normalized_key = self._normalize_key(key)
        if self._redis_sync is not None:
            self._redis_sync.delete(normalized_key)
            return

        with self._lock:
            self._items.pop(normalized_key, None)

    async def delete_prefix(self, prefix: str):
        normalized_prefix = self._normalize_key(prefix)
        if self._redis_async is not None:
            keys = [key async for key in self._redis_async.scan_iter(f"{normalized_prefix}*")]
            if keys:
                await self._redis_async.delete(*keys)
            return

        with self._lock:
            self._prune_memory()
            for key in [
                item_key for item_key in self._items.keys() if item_key.startswith(normalized_prefix)
            ]:
                self._items.pop(key, None)

    def delete_prefix_sync(self, prefix: str):
        normalized_prefix = self._normalize_key(prefix)
        if self._redis_sync is not None:
            keys = list(self._redis_sync.scan_iter(f"{normalized_prefix}*"))
            if keys:
                self._redis_sync.delete(*keys)
            return

        with self._lock:
            self._prune_memory()
            for key in [
                item_key for item_key in self._items.keys() if item_key.startswith(normalized_prefix)
            ]:
                self._items.pop(key, None)

    async def increment(
        self,
        key: str,
        ttl_seconds: float | int,
        amount: int = 1,
    ) -> int:
        normalized_key = self._normalize_key(key)
        ttl_value = max(int(ttl_seconds), 1)
        if self._redis_async is not None:
            value = int(await self._redis_async.incrby(normalized_key, int(amount)))
            if await self._redis_async.ttl(normalized_key) < 0:
                await self._redis_async.expire(normalized_key, ttl_value)
            return value

        with self._lock:
            found, current_value = self._get_memory_item(normalized_key)
            next_value = int(current_value or 0) + int(amount)
            self._items[normalized_key] = (
                monotonic() + ttl_value,
                next_value if found else next_value,
            )
            return next_value

    def increment_sync(
        self,
        key: str,
        ttl_seconds: float | int,
        amount: int = 1,
    ) -> int:
        normalized_key = self._normalize_key(key)
        ttl_value = max(int(ttl_seconds), 1)
        if self._redis_sync is not None:
            value = int(self._redis_sync.incrby(normalized_key, int(amount)))
            if self._redis_sync.ttl(normalized_key) < 0:
                self._redis_sync.expire(normalized_key, ttl_value)
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
        normalized_key = self._normalize_key(key)
        if self._redis_async is not None:
            ttl_value = int(await self._redis_async.ttl(normalized_key))
            return max(ttl_value, 0)

        with self._lock:
            found, _value = self._get_memory_item(normalized_key)
            if not found:
                return 0
            expires_at = self._items.get(normalized_key, (None, None))[0]
            if expires_at is None:
                return 0
            return max(int(expires_at - monotonic()), 0)

    def get_ttl_sync(self, key: str) -> int:
        normalized_key = self._normalize_key(key)
        if self._redis_sync is not None:
            ttl_value = int(self._redis_sync.ttl(normalized_key))
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
        if self._redis_async is not None:
            await self.delete_prefix("")
            return

        with self._lock:
            self._items.clear()

    def clear_sync(self):
        if self._redis_sync is not None:
            self.delete_prefix_sync("")
            return

        with self._lock:
            self._items.clear()

    async def close(self):
        if self._redis_async is not None:
            close = getattr(self._redis_async, "aclose", None) or getattr(self._redis_async, "close", None)
            if close is not None:
                result = close()
                if result is not None:
                    await result
        if self._redis_sync is not None:
            close = getattr(self._redis_sync, "close", None)
            if close is not None:
                close()

    def _normalize_key(self, key: str) -> str:
        normalized = str(key or "").strip()
        return f"{self.namespace}:{normalized}" if self.namespace else normalized

    def _normalize_ttl(self, ttl_seconds: float | int | None) -> int | None:
        if ttl_seconds is None:
            return None
        ttl_value = int(ttl_seconds)
        return max(ttl_value, 0)

    def _build_async_redis(self, redis_url: str | None, required: bool):
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

    def _build_sync_redis(self, redis_url: str | None, required: bool):
        if not redis_url:
            return None
        try:
            from redis import Redis

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
