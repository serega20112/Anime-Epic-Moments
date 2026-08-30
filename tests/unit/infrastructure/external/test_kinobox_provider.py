from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest

from backend.infrastructure.external import KinoboxProvider
from backend.infrastructure.external.errors import (
    ExternalServiceInvalidResponseError,
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)


class _FakeJsonResponse:
    def __init__(self, payload, content_length=None):
        self._payload = payload
        self.headers = {} if content_length is None else {"content-length": str(content_length)}

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


_PLAYERS = [
    {
        "source": "kodik",
        "translation": {"id": 610, "title": "AniLibria.TV"},
        "quality": "WEB-DL 1080p",
        "iframeUrl": "https://kodik.info/find-player?shikimoriID=5114",
    },
    {
        "source": "alloha",
        "translation": {"id": 1, "title": "Дубляж"},
        "quality": "",
        "iframeUrl": "//alloha.tv/player/abc",
    },
]


def _client() -> KinoboxProvider:
    return KinoboxProvider(
        base_url="https://kinobox.tv",
        enabled=True,
        timeout=8,
    )


@pytest.mark.asyncio
async def test_kinobox_maps_players_to_embed_sources():
    """Каждый плеер из API превращается в embed-источник."""
    provider = _client()
    provider.session.get = AsyncMock(return_value=_FakeJsonResponse(_PLAYERS))

    items = await provider.search_sources(title="Test Anime", episode=1)

    assert [item.translation_name for item in items] == ["AniLibria.TV", "Дубляж"]
    assert all(item.source_type == "embed" for item in items)
    assert all(item.provider_name == "Kinobox" for item in items)
    assert items[0].quality_label == "WEB-DL 1080p"
    assert items[0].stream_url == "https://kodik.info/find-player?shikimoriID=5114"


@pytest.mark.asyncio
async def test_kinobox_normalizes_protocol_relative_urls():
    """Ссылки вида //host нормализуются до https."""
    provider = _client()
    provider.session.get = AsyncMock(return_value=_FakeJsonResponse(_PLAYERS))

    items = await provider.search_sources(title="Test Anime", episode=1)

    assert items[1].stream_url == "https://alloha.tv/player/abc"
    assert items[1].quality_label == "Auto"


@pytest.mark.asyncio
async def test_kinobox_dedupes_same_iframe():
    """Дубликаты iframeUrl отбрасываются."""
    provider = _client()
    provider.session.get = AsyncMock(return_value=_FakeJsonResponse([_PLAYERS[0], _PLAYERS[0]]))

    items = await provider.search_sources(title="Test Anime", episode=1)

    assert len(items) == 1


@pytest.mark.asyncio
async def test_kinobox_falls_back_to_source_label_without_translation():
    """Без названия озвучки подписью становится метка балансера."""
    provider = _client()
    provider.session.get = AsyncMock(
        return_value=_FakeJsonResponse([{"source": "collaps", "iframeUrl": "https://c.tv/p/1"}])
    )

    items = await provider.search_sources(title="Test Anime", episode=1)

    assert items[0].translation_name == "Collaps"
    assert items[0].source_name == "kinobox-collaps"


@pytest.mark.asyncio
async def test_kinobox_disabled_returns_nothing():
    """Disabled провайдер не выполняет сетевых запросов."""
    provider = KinoboxProvider(base_url="https://kinobox.tv", enabled=False, timeout=8)
    provider.session.get = AsyncMock(side_effect=AssertionError("must not be called"))

    assert await provider.search_sources(title="Test Anime", episode=1) == []


@pytest.mark.asyncio
async def test_kinobox_invalid_payload_raises():
    """Невалидный JSON-ответ — malformed response."""
    provider = _client()
    provider.session.get = AsyncMock(return_value=_FakeJsonResponse({"unexpected": True}))

    with pytest.raises(ExternalServiceInvalidResponseError):
        await provider.search_sources(title="Test Anime", episode=1)


@pytest.mark.asyncio
async def test_kinobox_rejects_oversized_body_without_reading():
    """Ответ с гигантским Content-Length отклоняется до чтения тела."""
    provider = _client()

    def _must_not_read():
        raise AssertionError("body must not be read")

    response = _FakeJsonResponse([], content_length=10 * 1024 * 1024 + 1)
    response.json = _must_not_read
    provider.session.get = AsyncMock(return_value=response)

    with pytest.raises(ExternalServiceInvalidResponseError):
        await provider.search_sources(title="Test Anime", episode=1)


@pytest.mark.asyncio
async def test_kinobox_timeout_raises():
    """Таймаут транслируется в ExternalServiceTimeoutError."""
    provider = _client()
    provider.session.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    with pytest.raises(ExternalServiceTimeoutError):
        await provider.search_sources(title="Test Anime", episode=1)


@pytest.mark.asyncio
async def test_kinobox_unavailable_raises():
    """Сбой сети транслируется в ExternalServiceUnavailableError."""
    provider = _client()
    provider.session.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

    with pytest.raises(ExternalServiceUnavailableError):
        await provider.search_sources(title="Test Anime", episode=1)
