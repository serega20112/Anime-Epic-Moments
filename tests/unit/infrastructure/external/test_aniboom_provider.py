from __future__ import annotations

import json
from unittest.mock import AsyncMock

import httpx
import pytest

from backend.infrastructure.external import AniBoomProvider
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


def _client() -> AniBoomProvider:
    return AniBoomProvider(
        base_url="https://aniboom.one",
        enabled=True,
        timeout=8,
    )


def _embed_html() -> str:
    data = {
        "id": "x",
        "hls": json.dumps(
            {"src": "https://cdn.example.com/master.m3u8", "type": "application/x-mpegURL"},
            separators=(",", ":"),
        ),
        "dash": json.dumps(
            {"src": "https://cdn.example.com/master.mpd", "type": "application/dash+xml"},
            separators=(",", ":"),
        ),
    }
    raw_attr = json.dumps(data, separators=(",", ":")).replace('"', "&quot;")
    return f'<div id="video" data-parameters="{raw_attr}"></div>'


def test_aniboom_extracts_hls_from_embed() -> None:
    provider = _client()
    provider.session.get = AsyncMock(return_value=_FakeTextResponse(_embed_html()))

    items = provider.extract_embed("https://aniboom.one/embed/x?episode=1&translation=30")

    assert len(items) == 1
    assert items[0].quality_label == "1080"
    assert items[0].stream_url == "https://cdn.example.com/master.m3u8"
    assert items[0].provider_name == "AniBoom"


def test_aniboom_extract_falls_back_to_dash() -> None:
    data = json.dumps(
        {
            "id": "x",
            "dash": json.dumps(
                {"src": "https://cdn.example.com/master.mpd"}, separators=(",", ":")
            ),
        },
        separators=(",", ":"),
    ).replace('"', "&quot;")
    page = f'<div id="video" data-parameters="{data}"></div>'
    provider = _client()
    provider.session.get = AsyncMock(return_value=_FakeTextResponse(page))

    items = provider.extract_embed("https://aniboom.one/embed/x")

    assert items[0].stream_url == "https://cdn.example.com/master.mpd"


def test_aniboom_extract_no_sources_without_stream() -> None:
    data = json.dumps({"id": "x"}).replace('"', "&quot;")
    page = f'<div id="video" data-parameters="{data}"></div>'
    provider = _client()
    provider.session.get = AsyncMock(return_value=_FakeTextResponse(page))

    assert provider.extract_embed("https://aniboom.one/embed/x") == []


def test_aniboom_unparsable_page_raises() -> None:
    provider = _client()
    provider.session.get = AsyncMock(return_value=_FakeTextResponse("<html>no player</html>"))

    with pytest.raises(ExternalServiceInvalidResponseError):
        provider.extract_embed("https://aniboom.one/embed/x")


def test_aniboom_timeout_raises() -> None:
    provider = _client()
    provider.session.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    with pytest.raises(ExternalServiceTimeoutError):
        provider.extract_embed("https://aniboom.one/embed/x")


def test_aniboom_unavailable_raises() -> None:
    provider = _client()
    provider.session.get = AsyncMock(side_effect=httpx.ConnectError("boom"))

    with pytest.raises(ExternalServiceUnavailableError):
        provider.extract_embed("https://aniboom.one/embed/x")


def test_aniboom_search_sources_returns_empty_without_index() -> None:
    """У AniBoom нет публичного индекса по тайтлу — поиск пуст."""
    provider = _client()
    assert provider.search_sources(title="Test", episode=1) == []
