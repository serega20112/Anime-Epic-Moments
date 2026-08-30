from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest

from backend.infrastructure.external import EpornerProvider
from backend.infrastructure.external.eporner_provider import _calc_hash
from backend.infrastructure.external.errors import (
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)


class _FakeJsonResponse:
    def __init__(self, payload: dict, text: str = ""):
        self._payload = payload
        self.text = text

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


def _page_html(page_hash: str = "2a8179fe3f46d2bc83a17a6a59c954c0") -> str:
    return (
        '<html><script>var player = "x"; '
        f'hash = "{page_hash}";'
        '</script><video data-vid="x/x.mp4"></video></html>'
    )


def _xhr_payload(src: str = "https://vid.example.com/18085480-720p.mp4") -> dict:
    return {
        "available": True,
        "sources": {
            "mp4": {
                "720p HD": {
                    "labelShort": "720p",
                    "src": src,
                    "type": "video/mp4",
                    "default": True,
                },
                "480p": {
                    "labelShort": "480p",
                    "src": src.replace("720p", "480p"),
                    "type": "video/mp4",
                },
            }
        },
    }


def _provider(enabled: bool = True) -> EpornerProvider:
    return EpornerProvider(base_url="https://www.eporner.com", enabled=enabled, timeout=10)


@pytest.mark.asyncio
async def test_eporner_searches_and_extracts_direct_mp4():
    """Поиск → страница видео (hash) → xhr → прямые MP4 всех качеств."""
    provider = _provider()
    search_payload = {
        "videos": [
            {"id": "i2VSqDiCBlR", "title": "Bible Black 01 720p", "keywords": ""},
        ]
    }
    provider.session.get = AsyncMock(
        side_effect=[
            _FakeJsonResponse(search_payload),
            _FakeJsonResponse({}, text=_page_html()),
            _FakeJsonResponse(_xhr_payload()),
        ]
    )

    items = await provider.search_sources(title="Bible Black", episode=1)

    assert len(items) == 2
    first, second = items
    assert first.provider_name == "Eporner"
    assert first.episode == 1
    assert first.language == "ja"
    assert first.quality_label == "720p"
    assert first.stream_url == "https://vid.example.com/18085480-720p.mp4"
    assert second.quality_label == "480p"
    assert provider.session.get.await_count == 3


@pytest.mark.asyncio
async def test_eporner_filters_irrelevant_videos():
    """Непохожие видео отфильтровываются до запроса потоков."""
    provider = _provider()
    search_payload = {
        "videos": [
            {"id": "irr0", "title": "This BUSTY TEEN Skips BIBLE STUDY", "keywords": ""},
            {"id": "i2VSqDiCBlR", "title": "Bible Black uncensored episode 1", "keywords": ""},
        ]
    }
    provider.session.get = AsyncMock(
        side_effect=[
            _FakeJsonResponse(search_payload),
            _FakeJsonResponse({}, text=_page_html()),
            _FakeJsonResponse(_xhr_payload()),
        ]
    )

    items = await provider.search_sources(title="Bible Black", episode=1)

    assert {item.source_name for item in items} == {"eporner-i2VSqDiCBlR"}
    assert len(items) == 2
    assert provider.session.get.await_count == 3


@pytest.mark.asyncio
async def test_eporner_returns_nothing_when_disabled():
    """Выключенный провайдер не выполняет сетевых запросов."""
    provider = _provider(enabled=False)
    provider.session.get = AsyncMock(side_effect=AssertionError("must not be called"))

    assert await provider.search_sources(title="Bible Black", episode=1) == []


@pytest.mark.asyncio
async def test_eporner_empty_search_results():
    """Пустая выдача поиска даёт пустой результат без ошибок."""
    provider = _provider()
    provider.session.get = AsyncMock(
        return_value=_FakeJsonResponse({"videos": [], "total_count": 0})
    )

    assert await provider.search_sources(title="Monster Farm", episode=1) == []


@pytest.mark.asyncio
async def test_eporner_timeout_returns_empty():
    """Таймаут поиска деградирует в пустой результат (без подъёма 500)."""
    provider = _provider()
    provider.session.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    assert await provider.search_sources(title="Bible Black", episode=1) == []


@pytest.mark.asyncio
async def test_eporner_network_error_returns_empty():
    """Сбой сети поиска деградирует в пустой результат."""
    provider = _provider()
    provider.session.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

    assert await provider.search_sources(title="Bible Black", episode=1) == []


@pytest.mark.asyncio
async def test_eporner_missing_hash_skips_video():
    """Видео без hash на странице пропускается без ошибок."""
    provider = _provider()
    search_payload = {"videos": [{"id": "i2VSqDiCBlR", "title": "Bible Black 01", "keywords": ""}]}
    provider.session.get = AsyncMock(
        side_effect=[
            _FakeJsonResponse(search_payload),
            _FakeJsonResponse({}, text="<html>no hash here</html>"),
        ]
    )

    items = await provider.search_sources(title="Bible Black", episode=1)

    assert items == []
    assert provider.session.get.await_count == 2


@pytest.mark.asyncio
async def test_eporner_transport_errors_type_map():
    """Транспортные ошибки внутренних запросов транслируются корректно."""
    checks = [
        (httpx.TimeoutException("t"), ExternalServiceTimeoutError),
        (httpx.ConnectError("c"), ExternalServiceUnavailableError),
    ]
    for exc_type, mapped_type in checks:
        provider = _provider()
        provider.session.get = AsyncMock(side_effect=exc_type)
        with pytest.raises(mapped_type):
            await provider._video_streams("i2VSqDiCBlR")


@pytest.mark.asyncio
async def test_eporner_hls_fallback():
    """Когда MP4 нет, но есть HLS — используются HLS-потоки."""
    provider = _provider()
    search_payload = {"videos": [{"id": "abc123XYZ", "title": "Bible Black 01", "keywords": ""}]}
    hls_payload = {
        "available": True,
        "sources": {
            "hls": {
                "hls-720": {"labelShort": "720p", "src": "https://cdn.example.com/index.m3u8"},
            }
        },
    }
    provider.session.get = AsyncMock(
        side_effect=[
            _FakeJsonResponse(search_payload),
            _FakeJsonResponse({}, text=_page_html()),
            _FakeJsonResponse(hls_payload),
        ]
    )

    items = await provider.search_sources(title="Bible Black", episode=1)

    assert len(items) == 1
    assert items[0].stream_url == "https://cdn.example.com/index.m3u8"
    assert items[0].quality_label == "720p"


@pytest.mark.asyncio
async def test_calc_hash_matches_live_example():
    """Ответ r.jhash совпадает с live-примером (2a8179fe...) → bsktfihk1who10itmqyowuny8."""
    assert _calc_hash("2a8179fe3f46d2bc83a17a6a59c954c0") == "bsktfihk1who10itmqyowuny8"
