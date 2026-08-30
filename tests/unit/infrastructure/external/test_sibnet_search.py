"""Тесты текстового поиска Sibnet по названию тайтла."""

from unittest.mock import AsyncMock, patch

import pytest

from backend.infrastructure.external.errors import ExternalServiceUnavailableError
from backend.infrastructure.external.sibnet_provider import SibnetProvider

pytestmark = pytest.mark.unit


def _provider() -> SibnetProvider:
    return SibnetProvider(base_url="https://video.sibnet.ru", enabled=True, timeout=5)


_SEARCH_PAGE = (
    '<div><a href="/shell.php?videoid=111">Anime 1</a>'
    '<a href="/shell.php?videoid=222">Anime 2</a>'
    '<a href="/shell.php?videoid=111">dup</a></div>'
)


class TestSibnetSearchSources:
    async def test_search_by_title_finds_streams(self):
        provider = _provider()
        with (
            patch.object(provider, "_fetch", new=AsyncMock(return_value=_SEARCH_PAGE)) as fetch,
            patch.object(
                provider,
                "extract_embed",
                new=AsyncMock(return_value=[object()]),
            ) as extract,
        ):
            result = await provider.search_sources("Необъятный океан", episode=3)
        fetch.assert_awaited_once()
        assert "search=" in fetch.await_args.args[0]
        extract.assert_any_call("https://video.sibnet.ru/shell.php?videoid=111", 3)
        extract.assert_any_call("https://video.sibnet.ru/shell.php?videoid=222", 3)
        assert len(result) == 2

    async def test_search_dedupes_video_ids(self):
        provider = _provider()
        with (
            patch.object(provider, "_fetch", new=AsyncMock(return_value=_SEARCH_PAGE)),
            patch.object(
                provider, "extract_embed", new=AsyncMock(return_value=[object()])
            ) as extract,
        ):
            await provider.search_sources("title", episode=1)
        assert extract.await_count == 2

    async def test_search_stops_at_limit(self):
        provider = _provider()
        page = "".join(f'<a href="/shell.php?videoid={n}">t</a>' for n in range(1, 20))
        with (
            patch.object(provider, "_fetch", new=AsyncMock(return_value=page)),
            patch.object(provider, "extract_embed", new=AsyncMock(return_value=[object()])),
        ):
            result = await provider.search_sources("title", episode=1, limit=3)
        assert len(result) == 3

    async def test_search_returns_empty_on_service_error(self):
        provider = _provider()
        with patch.object(
            provider,
            "_fetch",
            new=AsyncMock(side_effect=ExternalServiceUnavailableError(service_name="Sibnet")),
        ):
            result = await provider.search_sources("title", episode=1)
        assert result == []

    async def test_search_disabled_provider(self):
        provider = SibnetProvider(base_url="https://video.sibnet.ru", enabled=False, timeout=5)
        assert await provider.search_sources("title", episode=1) == []
