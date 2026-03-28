from __future__ import annotations

import pytest

from src.backend.infrastructure.cache import key_value_store as store_module
from src.backend.infrastructure.cache.key_value_store import KeyValueStore


def test_key_value_store_reads_written_values_without_redis():
    """Проверяем, что KeyValueStore сохраняет и возвращает значения в memory-fallback режиме."""
    store = KeyValueStore(redis_url=None, namespace="test")

    store.set("alpha", {"value": 1}, ttl_seconds=30)

    assert store.get("alpha") == {"value": 1}


def test_key_value_store_expires_values_in_memory(monkeypatch):
    """Проверяем, что KeyValueStore удаляет записи после истечения TTL в памяти."""
    current_time = {"value": 10.0}
    monkeypatch.setattr(store_module, "monotonic", lambda: current_time["value"])
    store = KeyValueStore(redis_url=None, namespace="test")

    store.set("alpha", 7, ttl_seconds=5)
    current_time["value"] = 20.0

    assert store.get("alpha") is None
    assert store.contains("alpha") is False


@pytest.mark.parametrize(
    ("operations", "expected"),
    [
        ([("increment", "k", 10), ("increment", "k", 10)], 2),
        ([("increment", "other", 5)], 1),
    ],
)
def test_key_value_store_increments_counters(operations, expected):
    """Проверяем, что KeyValueStore считает инкременты в memory-fallback режиме."""
    store = KeyValueStore(redis_url=None, namespace="test")
    result = 0

    for _action, key, ttl in operations:
        result = store.increment(key, ttl_seconds=ttl)

    assert result == expected


def test_key_value_store_deletes_by_prefix():
    """Проверяем, что KeyValueStore умеет удалять записи по общему префиксу."""
    store = KeyValueStore(redis_url=None, namespace="test")
    store.set("group:1", 1, ttl_seconds=30)
    store.set("group:2", 2, ttl_seconds=30)
    store.set("single", 3, ttl_seconds=30)

    store.delete_prefix("group:")

    assert store.get("group:1") is None
    assert store.get("group:2") is None
    assert store.get("single") == 3
