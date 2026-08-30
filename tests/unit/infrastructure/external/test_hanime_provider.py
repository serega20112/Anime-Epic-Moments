from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from curl_cffi.requests.exceptions import Timeout as CurlTimeout

from backend.infrastructure.external import HanimeProvider
from backend.infrastructure.external.errors import ExternalServiceTimeoutError


class _FakeJsonResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def _client() -> HanimeProvider:
    return HanimeProvider(
        base_url="https://hanime.tv",
        enabled=True,
        timeout=10,
    )


def _search_payload() -> dict:
    return {
        "hentai_videos": [
            {
                "id": 111,
                "name": "Ero Zemi: Ecchi ni Yaruki ni ABC",
                "original_title": "エロゼミ",
                "released_at": "2021-07-04",
            },
            {"id": 222, "name": "Совершенно другой тайтл", "released_at": "2015-01-01"},
            {
                "id": 333,
                "name": "ero zemi ecchi ni yaruki ni abc the completion",
                "released_at": "2022-01-01",
            },
        ]
    }


def _video_payload(video_id: int) -> dict:
    return {
        "video_streams_url": [
            f"https://mushy.tv/hls/{video_id}/master.m3u8",
        ]
    }


def test_hanime_search_returns_relevant_sources() -> None:
    provider = _client()
    provider.session.post = AsyncMock(return_value=_FakeJsonResponse(_search_payload()))

    def fake_get(url, params=None):
        return _FakeJsonResponse(_video_payload(int(params["id"])))

    provider.session.get = AsyncMock(side_effect=fake_get)

    items = provider.search_sources(title="Ero Zemi: Ecchi ni Yaruki ni ABC", episode=1)

    assert [item.episode for item in items] == [1, 1]
    ids = {item.source_name for item in items}
    assert ids == {"hanime-111", "hanime-333"}
    assert all(item.stream_url.endswith(".m3u8") for item in items)
    assert all(item.provider_name == "Hanime" for item in items)
    assert all(item.translation_name == "Hanime" for item in items)


def test_hanime_search_empty_without_results() -> None:
    provider = _client()
    provider.session.post = AsyncMock(return_value=_FakeJsonResponse({}))

    assert provider.search_sources(title="Unknown", episode=1) == []


def test_hanime_search_skips_video_without_streams() -> None:
    provider = _client()
    provider.session.post = AsyncMock(return_value=_FakeJsonResponse(_search_payload()))
    provider.session.get = AsyncMock(return_value=_FakeJsonResponse({"video_streams_url": []}))

    assert provider.search_sources(title="Ero Zemi Ecchi ni Yaruki ni ABC", episode=3) == []


def test_hanime_year_mismatch_filters_candidate() -> None:
    provider = _client()
    payload = {
        "videos": [
            {"id": 111, "name": "ero zemi", "released_at": "1999-01-01"},
        ]
    }
    provider.session.post = AsyncMock(return_value=_FakeJsonResponse(payload))
    provider.session.get = AsyncMock(return_value=_FakeJsonResponse(_video_payload(111)))

    assert provider.search_sources(title="ero zemi", episode=1, year=2021) == []


def test_hanime_quality_from_stream_url() -> None:
    provider = _client()
    payload = {"videos": [{"id": 444, "name": "ero zemi"}]}
    streams = {"video_streams_url": ["https://mushy.tv/hls/444/1080/index.m3u8"]}
    provider.session.post = AsyncMock(return_value=_FakeJsonResponse(payload))
    provider.session.get = AsyncMock(return_value=_FakeJsonResponse(streams))

    items = provider.search_sources(title="ero zemi", episode=1)

    assert items[0].quality_label == "1080"


def test_hanime_timeout_raises() -> None:
    provider = _client()

    async def raise_timeout(*args, **kwargs):
        raise CurlTimeout("timeout")

    provider.session.post = raise_timeout

    with pytest.raises(ExternalServiceTimeoutError):
        provider.search_sources(title="ero zemi", episode=1)


def test_hanime_disabled_provider_is_not_active() -> None:
    provider = HanimeProvider(base_url="https://hanime.tv", enabled=False, timeout=10)

    assert provider.is_enabled() is False
