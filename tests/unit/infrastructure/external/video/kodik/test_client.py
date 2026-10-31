from __future__ import annotations

import base64
from unittest.mock import AsyncMock

import httpx
import pytest

from backend.infrastructure.external import KodikClient


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.headers = {}

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("//kodik.example/player", "https://kodik.example/player"),
        ("/seria/123/hash/720p", "https://kodikplayer.com/seria/123/hash/720p"),
        ("https://kodik.example/player", "https://kodik.example/player"),
    ],
)
def test_kodik_client_normalizes_links(value, expected):
    """Проверяем, что KodikClient нормализует protocol-relative и root-relative ссылки."""
    assert KodikClient()._normalize_link(value) == expected


def test_kodik_client_parses_player_link_and_maps_translation_type():
    """Проверяем, что KodikClient разбирает player link и нормализует тип перевода."""
    client = KodikClient()

    parsed = client._parse_link("https://kodik.example/seria/123/abcdef/720p")

    assert parsed == {
        "host": "kodik.example",
        "type": "seria",
        "id": "123",
        "hash": "abcdef",
        "quality": "720p",
    }
    assert client._map_translation_type("subtitles") == "sub"
    assert client._map_translation_type("voice") == "voice"


def _shift_minus_18(encoded: str) -> str:
    shifted = []
    for char in encoded:
        if "A" <= char <= "Z":
            code = ord(char) - 18
            if code < ord("A"):
                code += 26
            shifted.append(chr(code))
        elif "a" <= char <= "z":
            code = ord(char) - 18
            if code < ord("a"):
                code += 26
            shifted.append(chr(code))
        else:
            shifted.append(char)
    return "".join(shifted)


@pytest.mark.parametrize("strip_padding", [False, True])
def test_kodik_client_decodes_shifted_base64_source(strip_padding):
    """Проверяем, что KodikClient декодирует obfuscated src из ответа player API."""
    client = KodikClient()
    original = "https://cdn.example.com/master.m3u8"
    encoded = base64.b64encode(original.encode("utf-8")).decode("utf-8")
    if strip_padding:
        encoded = encoded.rstrip("=")

    decoded = client._decode_kodik_src(_shift_minus_18(encoded))

    assert decoded == original


async def test_kodik_client_search_sources_maps_results(monkeypatch):
    """Проверяем, что KodikClient превращает поисковый payload в набор discovered sources."""
    client = KodikClient()
    client.api_token = "token"
    client.session.get = AsyncMock(
        return_value=_FakeResponse(
            {
                "results": [
                    {
                        "title": "Gintama",
                        "translation": {"title": "AniLibria", "type": "voice"},
                        "link": "https://kodik.example/seria/123/abcdef/720p",
                        "seasons": {
                            "1": {"episodes": {"2": "https://kodik.example/seria/123/abcdef/720p"}}
                        },
                    }
                ]
            }
        )
    )

    async def _fake_video_links(link):
        return {
            "1080": [{"src": "https://cdn.example.com/1080.m3u8"}],
            "720": [{"src": "https://cdn.example.com/720.m3u8"}],
        }

    monkeypatch.setattr(client, "_get_video_links", _fake_video_links)

    items = await client.search_sources(title="Gintama", episode=2)

    assert [(item.translation_name, item.quality_label) for item in items] == [
        ("AniLibria", "1080"),
        ("AniLibria", "720"),
    ]


async def test_kodik_client_search_sources_follows_next_page(monkeypatch):
    """KodikClient обходит страницы поисковой выдачи, пока API отдаёт next_page."""
    client = KodikClient()
    client.api_token = "token"
    client._working_token = "token"

    def _material(mid: int) -> dict:
        episode_link = f"https://kodik.example/seria/{mid}/abcdef/720p"
        return {
            "title": "Gintama",
            "translation": {"title": "AniLibria", "type": "voice"},
            "link": episode_link,
            "seasons": {"1": {"episodes": {"2": episode_link}}},
        }

    first_page = _FakeResponse(
        {
            "results": [_material(111)],
            "next_page": "/search?title=Gintama&after=movie-111",
        }
    )
    second_page = _FakeResponse({"results": [_material(222)]})
    client.session.get = AsyncMock(side_effect=[first_page, second_page])

    async def _fake_video_links(link):
        return {"720": [{"src": f"https://cdn.example.com/{link}.m3u8"}]}

    monkeypatch.setattr(client, "_get_video_links", _fake_video_links)

    items = await client.search_sources(title="Gintama", episode=2)

    assert client.session.get.await_count == 2
    assert len(items) == 2
    assert {item.source_name for item in items} == {
        "https://kodik.example/seria/111/abcdef/720p",
        "https://kodik.example/seria/222/abcdef/720p",
    }


async def test_kodik_client_probe_failure_enables_backoff():
    """После провала probe всех токенов повторные поиски не дёргают сеть."""
    client = KodikClient()
    client.api_token = "dead-token"
    client.session.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

    assert await client.search_sources(title="First", episode=1) == []
    calls_after_first = client.session.get.await_count

    assert await client.search_sources(title="Second", episode=1) == []
    assert await client.search_sources(title="Third", episode=1) == []
    assert client.session.get.await_count == calls_after_first


async def test_kodik_client_working_token_skips_probes():
    """Подтверждённый рабочий токен переиспользуется без повторных probe-запросов."""
    client = KodikClient()
    client.api_token = "good-token"
    client.session.get = AsyncMock(return_value=_FakeResponse({"results": []}))

    assert await client.search_sources(title="First", episode=1) == []
    assert await client.search_sources(title="Second", episode=1) == []

    probe_calls = [
        call
        for call in client.session.get.await_args_list
        if call.kwargs.get("params", {}).get("limit") == 1
    ]
    assert len(probe_calls) == 1


@pytest.mark.parametrize(
    ("requested", "candidate", "expected"),
    [
        ("Блич", "Блич!", True),
        ("Блич", "Bleach", True),
        ("Блич", "Bleach: Sennen Kessen-hen", True),
        ("Блич", "Класс превосходства", False),
        ("Блич", "Класс превосходства: Classroom of the Elite", False),
        ("Gintama", "Gintama", True),
        ("Gintama", "Gintama: The Final", True),
        ("Gintama", "Gintama°", True),
        ("Ван Пис", "Класс превосходства", False),
    ],
)
async def test_kodik_client_looks_relevant_title_matching(requested, candidate, expected):
    """Релевантны только точные/расширенные совпадения тайтла, чужие — отклоняются."""
    client = KodikClient()

    assert (
        await client._looks_relevant(
            material={"title": candidate}, requested_title=requested, requested_year=None
        )
        is expected
    )


async def test_kodik_client_search_sources_skips_foreign_titles(monkeypatch):
    """Материалы другого тайтла из выдачи Kodik не попадают в результат."""
    client = KodikClient()
    client.api_token = "token"
    client._working_token = "token"
    client.session.get = AsyncMock(
        return_value=_FakeResponse(
            {
                "results": [
                    {
                        "title": "Класс превосходства",
                        "title_orig": "Classroom of the Elite",
                        "translation": {"title": "AniDub", "type": "voice"},
                        "link": "https://kodik.example/seria/999/badlink/720p",
                        "seasons": {
                            "1": {"episodes": {"1": "https://kodik.example/seria/999/badlink/720p"}}
                        },
                    },
                    {
                        "title": "Блич",
                        "title_orig": "Bleach",
                        "translation": {"title": "AniLibria", "type": "voice"},
                        "link": "https://kodik.example/seria/123/abcdef/720p",
                        "seasons": {
                            "1": {"episodes": {"1": "https://kodik.example/seria/123/abcdef/720p"}}
                        },
                    },
                ]
            }
        )
    )

    async def _fake_video_links(link):
        return {"720": [{"src": f"https://cdn.example.com/{link}.m3u8"}]}

    monkeypatch.setattr(client, "_get_video_links", _fake_video_links)

    items = await client.search_sources(title="Блич", episode=1)

    assert {item.source_name for item in items} == {"https://kodik.example/seria/123/abcdef/720p"}
