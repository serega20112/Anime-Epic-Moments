from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest

from backend.infrastructure.external import SibnetProvider
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


_SHELL_HTML = """
<html><body>
<iframe src="//video.sibnet.ru/player.phps?videoid=123&hash=abc"></iframe>
</body></html>
"""

_PLAYER_HTML = """
<script>
Player.init([{"file":"//video.sibnet.ru/mp4/999999.mp4"}]);
</script>
"""


def _client() -> SibnetProvider:
    return SibnetProvider(
        base_url="https://video.sibnet.ru",
        enabled=True,
        timeout=8,
    )


@pytest.mark.asyncio
async def test_sibnet_extracts_direct_mp4_from_shell():
    """Shell-страница → player-страница → прямой MP4."""
    provider = _client()
    provider.session.get = AsyncMock(
        side_effect=[
            _FakeTextResponse(_SHELL_HTML),
            _FakeTextResponse(_PLAYER_HTML),
        ]
    )

    items = await provider.extract_embed("https://video.sibnet.ru/shell.php?videoid=123")

    assert len(items) == 1
    item = items[0]
    assert item.source_type == "stream"
    assert item.stream_url == "https://video.sibnet.ru/mp4/999999.mp4"
    assert item.quality_label == "Auto"
    assert item.provider_name == "Sibnet"


@pytest.mark.asyncio
async def test_sibnet_reads_media_from_first_page_directly():
    """Если поток есть сразу на shell-странице — второй запрос не нужен."""
    provider = _client()
    direct_html = '<script>Player.init([{"file":"//video.sibnet.ru/mp4/1.mp4"}]);</script>'
    provider.session.get = AsyncMock(return_value=_FakeTextResponse(direct_html))

    items = await provider.extract_embed("https://video.sibnet.ru/shell.php?videoid=1")

    assert items[0].stream_url == "https://video.sibnet.ru/mp4/1.mp4"
    assert provider.session.get.await_count == 1


@pytest.mark.asyncio
async def test_sibnet_malformed_page_raises():
    """Страница без плеера и потока — malformed response."""
    provider = _client()
    provider.session.get = AsyncMock(return_value=_FakeTextResponse("<html>nothing</html>"))

    with pytest.raises(ExternalServiceInvalidResponseError):
        await provider.extract_embed("https://video.sibnet.ru/shell.php?videoid=1")


@pytest.mark.asyncio
async def test_sibnet_search_returns_nothing():
    """Поиск по названию не выполняет запросов, когда провайдер выключен."""
    provider = SibnetProvider(base_url="https://video.sibnet.ru", enabled=False, timeout=8)
    provider.session.get = AsyncMock(side_effect=AssertionError("must not be called"))

    assert await provider.search_sources(title="Test", episode=1) == []


@pytest.mark.asyncio
async def test_sibnet_disabled_returns_nothing():
    """Disabled экстрактор не выполняет сетевых запросов."""
    provider = SibnetProvider(base_url="https://video.sibnet.ru", enabled=False, timeout=8)
    provider.session.get = AsyncMock(side_effect=AssertionError("must not be called"))

    assert await provider.extract_embed("https://video.sibnet.ru/shell.php?videoid=1") == []


@pytest.mark.asyncio
async def test_sibnet_timeout_raises():
    """Таймаут транслируется в ExternalServiceTimeoutError."""
    provider = _client()
    provider.session.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    with pytest.raises(ExternalServiceTimeoutError):
        await provider.extract_embed("https://video.sibnet.ru/shell.php?videoid=1")


@pytest.mark.asyncio
async def test_sibnet_unavailable_raises():
    """Сбой сети транслируется в ExternalServiceUnavailableError."""
    provider = _client()
    provider.session.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

    with pytest.raises(ExternalServiceUnavailableError):
        await provider.extract_embed("https://video.sibnet.ru/shell.php?videoid=1")
