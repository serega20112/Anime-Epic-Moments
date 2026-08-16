from __future__ import annotations

import pytest

from backend.infrastructure.cache.ttl_cache import TTLCache
from backend.utils import ttl_cache as ttl_cache_module


@pytest.mark.unit
@pytest.mark.parametrize(
    ("actions", "expected"),
    [
        ([("set", "alpha", 1), ("get", "alpha", None)], 1),
        ([("set", "beta", 2), ("delete", "beta", None), ("get", "beta", "missing")], "missing"),
    ],
)
def test_ttl_cache_returns_values_for_live_entries(actions, expected):
    """Проверяем, что кэш отдает актуальные записи и не отдает удаленные."""
    cache = TTLCache[str, object](ttl_seconds=5, max_entries=4)

    for action, key, value in actions:
        if action == "set":
            cache.set(key, value)
        elif action == "delete":
            cache.delete(key)
        else:
            assert cache.get(key, value) == expected


@pytest.mark.unit
def test_ttl_cache_expires_entries_with_time(monkeypatch):
    """Проверяем, что запись исчезает после истечения TTL."""
    current_time = {"value": 10.0}
    monkeypatch.setattr(ttl_cache_module, "monotonic", lambda: current_time["value"])
    cache = TTLCache[str, int](ttl_seconds=5, max_entries=4)

    cache.set("anime", 7)
    current_time["value"] = 16.0

    assert cache.contains("anime") is False
    assert cache.get("anime") is None


@pytest.mark.unit
@pytest.mark.parametrize(
    ("keys", "predicate", "expected_keys"),
    [
        (
            [("rec:1", 1), ("rec:2", 2), ("search:1", 3)],
            lambda key: key.startswith("rec:"),
            {"search:1"},
        ),
        (
            [("watch:1", 1), ("watch:2", 2), ("favorite:1", 3)],
            lambda key: key.endswith(":2"),
            {"watch:1", "favorite:1"},
        ),
    ],
)
def test_ttl_cache_deletes_matching_keys(keys, predicate, expected_keys):
    """Проверяем, что delete_matching удаляет только подходящие ключи."""
    cache = TTLCache[str, int](ttl_seconds=30, max_entries=8)

    for key, value in keys:
        cache.set(key, value)

    cache.delete_matching(predicate)

    assert {key for key, _value in keys if cache.contains(key)} == expected_keys


@pytest.mark.unit
def test_ttl_cache_respects_max_entries():
    """Проверяем, что кэш ограничивает размер и выталкивает старые записи."""
    cache = TTLCache[str, int](ttl_seconds=30, max_entries=2)

    cache.set("first", 1)
    cache.set("second", 2)
    cache.set("third", 3)

    assert cache.contains("first") is False
    assert cache.get("second") == 2
    assert cache.get("third") == 3
