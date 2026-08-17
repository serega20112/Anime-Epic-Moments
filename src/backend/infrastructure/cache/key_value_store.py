from __future__ import annotations

import dataclasses
import datetime
import importlib
import json
from threading import RLock
from time import monotonic
from typing import Any

_DATACLASS_MARKER = "__dataclass__"
_DATETIME_MARKER = "__datetime__"


async def _encode(value: Any) -> Any:
    """Convert a value to JSON-native types, tagging dataclasses and datetimes."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            _DATACLASS_MARKER: f"{value.__class__.__module__}.{value.__class__.__qualname__}",
            "__fields__": {
                field.name: await _encode(getattr(value, field.name))
                for field in dataclasses.fields(value)
            },
        }
    if isinstance(value, datetime.datetime):
        return {_DATETIME_MARKER: value.isoformat()}
    if isinstance(value, (tuple, set)):
        return [await _encode(item) for item in value]
    if isinstance(value, list):
        return [await _encode(item) for item in value]
    if isinstance(value, dict):
        return {str(key): await _encode(item) for key, item in value.items()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"cannot serialize value of type {type(value).__name__}")


async def _resolve_class(qualified_name: str) -> type:
    """Resolve a ``module.QualifiedName`` string to the actual class."""
    module_name, class_name = qualified_name.rsplit(".", 1)
    module = importlib.import_module(module_name)
    for part in class_name.split("."):
        module = getattr(module, part)
    if not isinstance(module, type):
        raise TypeError(f"{qualified_name} does not name a class")
    return module


async def _decode(value: Any) -> Any:
    """Rebuild dataclasses and datetimes from a JSON-decoded structure."""
    if isinstance(value, dict):
        if _DATETIME_MARKER in value:
            return datetime.datetime.fromisoformat(value[_DATETIME_MARKER])
        if _DATACLASS_MARKER in value:
            cls = await _resolve_class(value[_DATACLASS_MARKER])
            fields = {key: await _decode(item) for key, item in value["__fields__"].items()}
            return cls(**fields)
        return {key: await _decode(item) for key, item in value.items()}
    if isinstance(value, list):
        return [await _decode(item) for item in value]
    return value


async def _serialize(value: Any) -> str:
    """Serialize a value to a JSON string with explicit tagging."""
    return json.dumps(await _encode(value), ensure_ascii=False, separators=(",", ":"))


async def _deserialize(raw_value: str, default: Any) -> Any:
    """Deserialize a JSON string, returning the default on corrupt payloads."""
    try:
        return await _decode(json.loads(raw_value))
    except (ValueError, TypeError, KeyError, AttributeError, ImportError):
        return default


class KeyValueStore:
    """Store arbitrary JSON-serializable values in Redis or an in-memory fallback.

    Domain dataclasses are stored with explicit type tags so the wire format is
    plain JSON without pickling.
    """

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

    async def ping(self) -> bool:
        """Check connectivity, returning True for the memory fallback.

        Returns:
            bool: True when the backing store responds.
        """
        if self._redis is None:
            return True
        try:
            return bool(await self._redis.ping())
        except Exception:
            self._redis = None
            return True

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

    async def _normalize_key(self, key: str) -> str:
        normalized = str(key or "").strip()
        return f"{self.namespace}:{normalized}" if self.namespace else normalized

    async def _normalize_ttl(self, ttl_seconds: float | int | None) -> int | None:
        if ttl_seconds is None:
            return None
        return max(int(ttl_seconds), 0)

    async def _get_memory_item(self, key: str) -> tuple[bool, Any]:
        await self._prune_memory()
        item = self._items.get(key)
        if item is None:
            return False, None
        expires_at, value = item
        if expires_at is not None and expires_at <= monotonic():
            self._items.pop(key, None)
            return False, None
        return True, value

    async def _prune_memory(self):
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
        normalized_key = await self._normalize_key(key)
        if self._redis is not None:
            try:
                return bool(await self._redis.exists(normalized_key))
            except Exception:
                self._redis = None

        with self._lock:
            found, _value = await self._get_memory_item(normalized_key)
            return found

    async def get(self, key: str, default: Any = None) -> Any:
        """Read a value by key.

        Args:
            key: Key to read.
            default: Value returned when the key is missing.

        Returns:
            Any: Stored value or default.
        """
        normalized_key = await self._normalize_key(key)
        if self._redis is not None:
            try:
                raw_value = await self._redis.get(normalized_key)
                if raw_value is None:
                    return default
                raw_text = raw_value.decode("utf-8") if isinstance(raw_value, bytes) else raw_value
                return await _deserialize(raw_text, default)
            except Exception:
                self._redis = None

        with self._lock:
            found, value = await self._get_memory_item(normalized_key)
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
        normalized_key = await self._normalize_key(key)
        ttl_value = await self._normalize_ttl(ttl_seconds)
        if ttl_value == 0:
            await self.delete(key)
            return value

        if self._redis is not None:
            try:
                payload = (await _serialize(value)).encode("utf-8")
                if ttl_value is None:
                    await self._redis.set(normalized_key, payload)
                else:
                    await self._redis.setex(normalized_key, ttl_value, payload)
                return value
            except Exception:
                self._redis = None

        expires_at = None if ttl_value is None else monotonic() + ttl_value
        with self._lock:
            await self._prune_memory()
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
        normalized_key = await self._normalize_key(key)
        ttl_value = await self._normalize_ttl(ttl_seconds)
        if ttl_value == 0:
            return False

        if self._redis is not None:
            try:
                payload = b"true"
                if ttl_value is None:
                    claimed = await self._redis.set(normalized_key, payload, nx=True)
                else:
                    claimed = await self._redis.set(normalized_key, payload, nx=True, ex=ttl_value)
                return bool(claimed)
            except Exception:
                self._redis = None

        expires_at = None if ttl_value is None else monotonic() + ttl_value
        with self._lock:
            await self._prune_memory()
            if normalized_key in self._items:
                return False
            self._items[normalized_key] = (expires_at, True)
        return True

    async def delete(self, key: str):
        """Remove a key.

        Args:
            key: Key to remove.
        """
        normalized_key = await self._normalize_key(key)
        if self._redis is not None:
            try:
                await self._redis.delete(normalized_key)
                return
            except Exception:
                self._redis = None

        with self._lock:
            self._items.pop(normalized_key, None)

    async def delete_prefix(self, prefix: str):
        """Remove all keys sharing a prefix.

        Args:
            prefix: Key prefix to remove.
        """
        normalized_prefix = await self._normalize_key(prefix)
        if self._redis is not None:
            try:
                keys = [key async for key in self._redis.scan_iter(f"{normalized_prefix}*")]
                if keys:
                    await self._redis.delete(*keys)
                return
            except Exception:
                self._redis = None

        with self._lock:
            await self._prune_memory()
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
        normalized_key = await self._normalize_key(key)
        ttl_value = max(int(ttl_seconds), 1)
        if self._redis is not None:
            try:
                value = int(await self._redis.incrby(normalized_key, int(amount)))
                if await self._redis.ttl(normalized_key) < 0:
                    await self._redis.expire(normalized_key, ttl_value)
                return value
            except Exception:
                self._redis = None

        with self._lock:
            _found, current_value = await self._get_memory_item(normalized_key)
            next_value = int(current_value or 0) + int(amount)
            self._items[normalized_key] = (
                monotonic() + ttl_value,
                next_value,
            )
            return next_value

    async def get_ttl(self, key: str) -> int:
        """Return the remaining TTL of a key.

        Args:
            key: Key to inspect.

        Returns:
            int: Remaining TTL in seconds.
        """
        normalized_key = await self._normalize_key(key)
        if self._redis is not None:
            try:
                ttl_value = int(await self._redis.ttl(normalized_key))
                return max(ttl_value, 0)
            except Exception:
                self._redis = None

        with self._lock:
            found, _value = await self._get_memory_item(normalized_key)
            if not found:
                return 0
            expires_at = self._items.get(normalized_key, (None, None))[0]
            if expires_at is None:
                return 0
            return max(int(expires_at - monotonic()), 0)

    async def clear(self):
        """Remove all stored keys."""
        if self._redis is not None:
            try:
                await self.delete_prefix("")
                return
            except Exception:
                self._redis = None

        with self._lock:
            self._items.clear()

    async def close(self):
        """Close the underlying Redis client."""
        if self._redis is not None:
            close = getattr(self._redis, "aclose", None) or getattr(self._redis, "close", None)
            if close is not None:
                try:
                    result = close()
                except Exception:
                    return
                if result is not None:
                    await result
