from __future__ import annotations

import pytest

from backend.infrastructure.cache import key_value_store as store_module
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.cache.security_store import SecurityKeyValueStore


class _FailingRedis:
    """Redis stub that raises on every IO operation."""

    def __getattr__(self, name):
        async def _fail(*args, **kwargs):
            raise ConnectionError("redis down")

        return _fail


class _WorkingRedis:
    """Redis stub, записывающий вызовы вместо реального подключения."""

    def __init__(self) -> None:
        """Создать пустой журнал вызовов."""
        self.calls: list[tuple[str, tuple]] = []

    async def set(self, *args, **kwargs):
        """Записать вызов set."""
        self.calls.append(("set", args))
        return True

    async def setex(self, *args, **kwargs):
        """Записать вызов setex."""
        self.calls.append(("setex", args))
        return True


@pytest.mark.unit
async def test_key_value_store_reads_written_values_without_redis():
    """Проверяем, что KeyValueStore сохраняет и возвращает значения в memory-fallback режиме."""
    store = KeyValueStore(redis_url=None, namespace="test")

    await store.set("alpha", {"value": 1}, ttl_seconds=30)

    assert await store.get("alpha") == {"value": 1}


@pytest.mark.unit
async def test_key_value_store_expires_values_in_memory(monkeypatch):
    """Проверяем, что KeyValueStore удаляет записи после истечения TTL в памяти."""
    current_time = {"value": 10.0}
    monkeypatch.setattr(store_module, "monotonic", lambda: current_time["value"])
    store = KeyValueStore(redis_url=None, namespace="test")

    await store.set("alpha", 7, ttl_seconds=5)
    current_time["value"] = 20.0

    assert await store.get("alpha") is None
    assert await store.contains("alpha") is False


@pytest.mark.unit
@pytest.mark.parametrize(
    ("operations", "expected"),
    [
        ([("increment", "k", 10), ("increment", "k", 10)], 2),
        ([("increment", "other", 5)], 1),
    ],
)
async def test_key_value_store_increments_counters(operations, expected):
    """Проверяем, что KeyValueStore считает инкременты в memory-fallback режиме."""
    store = KeyValueStore(redis_url=None, namespace="test")
    result = 0

    for _action, key, ttl in operations:
        result = await store.increment(key, ttl_seconds=ttl)

    assert result == expected


@pytest.mark.unit
async def test_key_value_store_deletes_by_prefix():
    """Проверяем, что KeyValueStore умеет удалять записи по общему префиксу."""
    store = KeyValueStore(redis_url=None, namespace="test")
    await store.set("group:1", 1, ttl_seconds=30)
    await store.set("group:2", 2, ttl_seconds=30)
    await store.set("single", 3, ttl_seconds=30)

    await store.delete_prefix("group:")

    assert await store.get("group:1") is None
    assert await store.get("group:2") is None
    assert await store.get("single") == 3


@pytest.mark.unit
async def test_key_value_store_consume_claims_key_once():
    """Проверяем, что KeyValueStore.consume атомарно забирает ключ только один раз."""
    store = KeyValueStore(redis_url=None, namespace="test")

    assert await store.consume("ticket", ttl_seconds=60) is True
    assert await store.consume("ticket", ttl_seconds=60) is False
    assert await store.consume("ticket", ttl_seconds=60) is False


@pytest.mark.unit
async def test_key_value_store_consume_rejects_zero_ttl():
    """Проверяем, что KeyValueStore.consume не забирает ключ при TTL <= 0."""
    store = KeyValueStore(redis_url=None, namespace="test")

    assert await store.consume("ticket", ttl_seconds=0) is False
    assert await store.contains("ticket") is False


@pytest.mark.unit
async def test_key_value_store_consume_respects_distinct_keys():
    """Проверяем, что KeyValueStore.consume считает разные ключи независимыми."""
    store = KeyValueStore(redis_url=None, namespace="test")

    assert await store.consume("alpha", ttl_seconds=60) is True
    assert await store.consume("beta", ttl_seconds=60) is True


@pytest.mark.unit
async def test_key_value_store_optional_redis_failure_falls_back_to_memory():
    """Проверяем, что KeyValueStore с required=False переходит в память при ошибке Redis."""
    store = KeyValueStore(redis_url=None, namespace="test")
    store._redis = _FailingRedis()
    store._redis_configured = True

    assert await store.get("alpha") is None
    assert store.uses_redis is False

    await store.set("alpha", 1, ttl_seconds=30)

    assert await store.get("alpha") == 1


@pytest.mark.unit
async def test_security_store_required_redis_failure_raises():
    """Проверяем, что SecurityKeyValueStore не деградирует в память при ошибке Redis."""
    store = SecurityKeyValueStore(redis_url=None, namespace="test")
    store._redis = _FailingRedis()
    store._redis_configured = True

    with pytest.raises(ConnectionError):
        await store.get("alpha")

    assert store.uses_redis is True


@pytest.mark.unit
async def test_key_value_store_increment_keeps_original_ttl_in_memory(monkeypatch):
    """Проверяем, что инкремент в памяти не продлевает TTL (фиксированное окно)."""
    current_time = {"value": 100.0}
    monkeypatch.setattr(store_module, "monotonic", lambda: current_time["value"])
    store = KeyValueStore(redis_url=None, namespace="test")

    await store.increment("counter", ttl_seconds=10)
    current_time["value"] = 105.0
    await store.increment("counter", ttl_seconds=10)

    assert await store.get_ttl("counter") == 5

    current_time["value"] = 111.0

    assert await store.get("counter") is None


@pytest.mark.unit
async def test_key_value_store_writes_serializable_value_to_redis():
    """Проверяем, что значение уходит в Redis сериализованным байтом с префиксом пространства."""
    redis = _WorkingRedis()
    store = KeyValueStore(redis_url=None, namespace="test")
    store._redis = redis

    await store.set("alpha", [1, 2], ttl_seconds=30)

    assert redis.calls == [("setex", ("test:alpha", 30, b"[1,2]"))]
    assert store.uses_redis is True


@pytest.mark.unit
async def test_key_value_store_unserializable_value_keeps_redis_enabled():
    """Проверяем, что несериализуемое значение не роняет Redis в память процесса.

    Регрессия: ошибка сериализации попадала в ветку сбоя IO, клиент Redis
    сбрасывался, и всё приложение тихо переходило на память воркера.
    """
    redis = _WorkingRedis()
    store = KeyValueStore(redis_url=None, namespace="test")
    store._redis = redis

    assert await store.set("alpha", object(), ttl_seconds=30) is not None

    assert redis.calls == []
    assert store.uses_redis is True
    assert await store.get("alpha") is None
