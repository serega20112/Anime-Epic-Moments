from __future__ import annotations

import pickle
from threading import RLock
from time import monotonic
from typing import Any


class KeyValueStore:
    """Хранит произвольные значения в Redis или в памяти с поддержкой TTL."""

    def __init__(
        self,
        redis_url: str | None = None,
        namespace: str = "anime_epic_moments",
        required: bool = False,
    ):
        self.namespace = str(namespace or "anime_epic_moments").strip(":")
        self._redis = self._build_redis(redis_url=redis_url, required=required)
        self._items: dict[str, tuple[float | None, Any]] = {}
        self._lock = RLock()

    @property
    def uses_redis(self) -> bool:
        return self._redis is not None

    def contains(self, key: str) -> bool:
        normalized_key = self._normalize_key(key)
        if self._redis is not None:
            return bool(self._redis.exists(normalized_key))

        with self._lock:
            found, _value = self._get_memory_item(normalized_key)
            return found

    def get(self, key: str, default: Any = None) -> Any:
        normalized_key = self._normalize_key(key)
        if self._redis is not None:
            raw_value = self._redis.get(normalized_key)
            if raw_value is None:
                return default
            return pickle.loads(raw_value)

        with self._lock:
            found, value = self._get_memory_item(normalized_key)
            return value if found else default

    def set(self, key: str, value: Any, ttl_seconds: float | int | None = None) -> Any:
        normalized_key = self._normalize_key(key)
        ttl_value = self._normalize_ttl(ttl_seconds)
        if ttl_value == 0:
            self.delete(key)
            return value

        if self._redis is not None:
            payload = pickle.dumps(value)
            if ttl_value is None:
                self._redis.set(normalized_key, payload)
            else:
                self._redis.setex(normalized_key, ttl_value, payload)
            return value

        expires_at = None if ttl_value is None else monotonic() + ttl_value
        with self._lock:
            self._prune_memory()
            self._items[normalized_key] = (expires_at, value)
        return value

    def delete(self, key: str):
        normalized_key = self._normalize_key(key)
        if self._redis is not None:
            self._redis.delete(normalized_key)
            return

        with self._lock:
            self._items.pop(normalized_key, None)

    def delete_prefix(self, prefix: str):
        normalized_prefix = self._normalize_key(prefix)
        if self._redis is not None:
            keys = list(self._redis.scan_iter(f"{normalized_prefix}*"))
            if keys:
                self._redis.delete(*keys)
            return

        with self._lock:
            self._prune_memory()
            for key in [
                item_key
                for item_key in self._items.keys()
                if item_key.startswith(normalized_prefix)
            ]:
                self._items.pop(key, None)

    def increment(
        self,
        key: str,
        ttl_seconds: float | int,
        amount: int = 1,
    ) -> int:
        normalized_key = self._normalize_key(key)
        ttl_value = max(int(ttl_seconds), 1)
        if self._redis is not None:
            value = int(self._redis.incrby(normalized_key, int(amount)))
            if self._redis.ttl(normalized_key) < 0:
                self._redis.expire(normalized_key, ttl_value)
            return value

        with self._lock:
            found, current_value = self._get_memory_item(normalized_key)
            next_value = int(current_value or 0) + int(amount)
            self._items[normalized_key] = (monotonic() + ttl_value, next_value)
            return next_value

    def get_ttl(self, key: str) -> int:
        normalized_key = self._normalize_key(key)
        if self._redis is not None:
            ttl_value = int(self._redis.ttl(normalized_key))
            return max(ttl_value, 0)

        with self._lock:
            found, _value = self._get_memory_item(normalized_key)
            if not found:
                return 0
            expires_at = self._items.get(normalized_key, (None, None))[0]
            if expires_at is None:
                return 0
            return max(int(expires_at - monotonic()), 0)

    def clear(self):
        if self._redis is not None:
            self.delete_prefix("")
            return

        with self._lock:
            self._items.clear()

    def _normalize_key(self, key: str) -> str:
        normalized = str(key or "").strip()
        return f"{self.namespace}:{normalized}" if self.namespace else normalized

    def _normalize_ttl(self, ttl_seconds: float | int | None) -> int | None:
        if ttl_seconds is None:
            return None
        ttl_value = int(ttl_seconds)
        return max(ttl_value, 0)

    def _build_redis(self, redis_url: str | None, required: bool):
        if not redis_url:
            return None
        try:
            import redis

            client = redis.Redis.from_url(
                redis_url,
                decode_responses=False,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            client.ping()
            return client
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
