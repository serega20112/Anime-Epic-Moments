from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest

from backend.infrastructure.external import ShikimoriClient


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.headers = {}

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeStore:
    """Минимальная замена KeyValueStore в памяти."""

    def __init__(self):
        self.data: dict[str, object] = {}

    async def get(self, key, default=None):
        return self.data.get(key, default)

    async def set(self, key, value, ttl_seconds=None):
        self.data[key] = value


def _make_client(payload=None, store=None) -> ShikimoriClient:
    client = ShikimoriClient(
        session=AsyncMock(), store=store, base_url="https://shikimori.test/api"
    )
    client.enabled = True
    if payload is not None:
        client.session.get = AsyncMock(return_value=_FakeResponse(payload))
    return client


@pytest.mark.unit
async def test_shikimori_client_returns_empty_when_disabled_or_no_ids():
    """Проверяем, что клиент не ходит в сеть, когда источник выключен или id не переданы."""
    client = _make_client(payload=[{"id": 1, "russian": "Тест"}])
    client.enabled = False

    assert await client.fetch_russian([1]) == {}
    client.session.get.assert_not_called()

    enabled_client = _make_client(payload=[{"id": 1, "russian": "Тест"}])
    assert await enabled_client.fetch_russian([]) == {}
    enabled_client.session.get.assert_not_called()


@pytest.mark.unit
async def test_shikimori_client_fetches_batch_in_single_request():
    """Проверяем, что пачка id запрашивается одним HTTP-вызовом без N+1."""
    payload = [
        {"id": 1, "russian": "У Коми проблемы с общением", "description": "Русское описание"},
        {"id": 2, "russian": None, "description": None},
    ]
    client = _make_client(payload=payload)

    result = await client.fetch_russian([1, 2, 3])

    client.session.get.assert_called_once()
    assert result[1] == ("У Коми проблемы с общением", "Русское описание")
    # Тайтл без русского названия и неизвестный id возвращают пустую пару.
    assert result[2] == (None, None)
    assert result[3] == (None, None)


@pytest.mark.unit
async def test_shikimori_client_caches_results_and_skips_repeat_requests():
    """Проверяем, что повторный запрос по закэшированным id не бьёт по Shikimori."""
    store = _FakeStore()
    client = _make_client(
        payload=[{"id": 5, "russian": "Тест", "description": "Описание"}], store=store
    )

    first = await client.fetch_russian([5])
    second = await client.fetch_russian([5])

    client.session.get.assert_called_once()
    assert first == second == {5: ("Тест", "Описание")}
    assert store.data["ru_title:5"] == "Тест"
    assert store.data["ru_desc:5"] == "Описание"


@pytest.mark.unit
async def test_shikimori_client_splits_large_batches():
    """Проверяем, что больше MAX_BATCH_SIZE id уходят несколькими чанками."""
    client = _make_client(payload=[])
    ids = list(range(1, 46))  # 45 id -> 3 чанка по 20/20/5

    await client.fetch_russian(ids)

    assert client.session.get.await_count == 3
    requested_ids = [call.kwargs["params"]["ids"] for call in client.session.get.await_args_list]
    assert requested_ids[0].count(",") == 19
    assert requested_ids[1].count(",") == 19
    assert requested_ids[2].count(",") == 4


@pytest.mark.unit
async def test_shikimori_client_degrades_gracefully_on_http_error():
    """Проверяем, что сетевая ошибка не роняет запрос — просто нет русских данных."""
    client = _make_client()
    client.session.get = AsyncMock(side_effect=httpx.ConnectError("network down"))

    result = await client.fetch_russian([1, 2])

    assert result == {}


@pytest.mark.unit
async def test_shikimori_client_cleans_values_and_ignores_bad_entries():
    """Проверяем, что мусорные значения ('null', не-числовые id) отфильтровываются."""
    payload = [
        {"id": 7, "russian": "  null  ", "description": "  "},
        {"id": "not-a-number", "russian": "Мусор"},
        "not-a-dict",
    ]
    client = _make_client(payload=payload)

    result = await client.fetch_russian([7])

    assert result == {7: (None, None)}


@pytest.mark.unit
async def test_shikimori_client_ignores_broken_cache_store():
    """Проверяем, что падение кэша не мешает получить данные из Shikimori."""
    store = _FakeStore()

    async def _broken_get(key, default=None):
        raise RuntimeError("redis down")

    store.get = _broken_get
    client = _make_client(payload=[{"id": 9, "russian": "Тест"}], store=store)

    result = await client.fetch_russian([9])

    assert result == {9: ("Тест", None)}
