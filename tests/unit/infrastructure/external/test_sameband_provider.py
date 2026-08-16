from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest

from backend.infrastructure.external import SamebandProvider
from backend.infrastructure.external.errors import (
    ExternalServiceInvalidResponseError,
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)


class _FakeTextResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        return None


_SEARCH_HTML = """
<div class="col-auto"><a class="image" href="/anime/20-test.html"></a>
<div class="poster" title="Test Anime"></div></div>
"""

_ANIME_HTML = """
<h1 class="p-0 m-0">Test Anime</h1>
<div class="player"><div class="player-content">
<iframe src="/pl/a/Test.html"></iframe></div></div>
"""

_PLAYER_HTML = '<script>var player = new Playerjs({id:"player",file:"/v/list/Test.txt"});</script>'

_PLAYLIST_TXT = """[
        {"file":"[480p]/v/e1_480p.m3u8,[720p]/v/e1_720p.m3u8","title":"1"},
        {"file":"[1080p]/v/e2_1080p.m3u8","title":"2"}
    ]"""


def _client() -> SamebandProvider:
    return SamebandProvider(
        base_url="https://sameband.studio",
        enabled=True,
        timeout=8,
    )


def _mock_pipeline(
    provider,
    *,
    search_html=_SEARCH_HTML,
    anime_html=_ANIME_HTML,
    player_html=_PLAYER_HTML,
    playlist=_PLAYLIST_TXT,
):
    provider._session.get = AsyncMock(
        side_effect=[
            _FakeTextResponse(search_html),
            _FakeTextResponse(anime_html),
            _FakeTextResponse(player_html),
            _FakeTextResponse(playlist),
        ]
    )
    return provider


@pytest.mark.asyncio
async def test_sameband_parses_multi_quality_sources():
    """Извлекаем несколько качеств одного эпизода из плейлиста SameBand."""
    provider = _mock_pipeline(_client())

    items = await provider.search_sources(title="Test Anime", episode=1)

    assert [item.quality_label for item in items] == ["480p", "720p"]
    assert all(item.episode == 1 for item in items)
    assert all(item.provider_name == "SameBand" for item in items)
    assert items[0].stream_url.startswith("https://sameband.studio/v/")


@pytest.mark.asyncio
async def test_sameband_ignores_missing_episode():
    """Несуществующий эпизод не даёт источников."""
    provider = _mock_pipeline(_client())

    assert await provider.search_sources(title="Test Anime", episode=99) == []


@pytest.mark.asyncio
async def test_sameband_disabled_returns_nothing():
    """Disabled провайдер не выполняет сетевых запросов."""
    provider = SamebandProvider(
        base_url="https://sameband.studio",
        enabled=False,
        timeout=8,
    )
    provider._session.get = AsyncMock(side_effect=AssertionError("must not be called"))

    assert await provider.search_sources(title="Test Anime", episode=1) == []


@pytest.mark.asyncio
async def test_sameband_empty_search_returns_nothing():
    """Пустой результат поиска не является ошибкой — нет источников."""
    provider = _client()
    provider._session.get = AsyncMock(return_value=_FakeTextResponse("<html>no results</html>"))

    assert await provider.search_sources(title="Missing", episode=1) == []


@pytest.mark.asyncio
async def test_sameband_timeout_raises():
    """Таймаут поиска транслируется в ExternalServiceTimeoutError."""
    provider = _client()
    provider._session.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    with pytest.raises(ExternalServiceTimeoutError):
        await provider.search_sources(title="Test Anime", episode=1)


@pytest.mark.asyncio
async def test_sameband_unavailable_raises():
    """Сбой сети транслируется в ExternalServiceUnavailableError."""
    provider = _client()
    provider._session.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

    with pytest.raises(ExternalServiceUnavailableError):
        await provider.search_sources(title="Test Anime", episode=1)


@pytest.mark.asyncio
async def test_sameband_malformed_player_raises():
    """Страница плеера без ожидаемого формата — malformed response."""
    provider = _mock_pipeline(_client(), player_html="<html>no player</html>")

    with pytest.raises(ExternalServiceInvalidResponseError):
        await provider.search_sources(title="Test Anime", episode=1)


@pytest.mark.asyncio
async def test_sameband_malformed_playlist_raises():
    """Плейлист, который нельзя распарсить, — malformed response."""
    provider = _mock_pipeline(_client(), playlist="<html>not a playlist</html>")

    with pytest.raises(ExternalServiceInvalidResponseError):
        await provider.search_sources(title="Test Anime", episode=1)
