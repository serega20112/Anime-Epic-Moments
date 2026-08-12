from __future__ import annotations

import base64
from unittest.mock import Mock

import pytest

from backend.infrastructure.external import KodikClient


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

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


def test_kodik_client_decodes_shifted_base64_source():
    """Проверяем, что KodikClient декодирует obfuscated src из ответа player API."""
    client = KodikClient()
    original = "https://cdn.example.com/master.m3u8"
    encoded = base64.b64encode(original.encode("utf-8")).decode("utf-8")
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

    decoded = client._decode_kodik_src("".join(shifted))

    assert decoded == original


def test_kodik_client_search_sources_maps_results(monkeypatch):
    """Проверяем, что KodikClient превращает поисковый payload в набор discovered sources."""
    client = KodikClient()
    client.api_token = "token"
    client.session.get = Mock(
        return_value=_FakeResponse(
            {
                "results": [
                    {
                        "title": "Gintama",
                        "translation": {"title": "AniLibria", "type": "voice"},
                        "link": "https://kodik.example/seria/123/abcdef/720p",
                    }
                ]
            }
        )
    )
    monkeypatch.setattr(
        client,
        "_get_video_links",
        lambda link: {
            "1080": [{"src": "https://cdn.example.com/1080.m3u8"}],
            "720": [{"src": "https://cdn.example.com/720.m3u8"}],
        },
    )

    items = client.search_sources(title="Gintama", episode=2)

    assert [(item.translation_name, item.quality_label) for item in items] == [
        ("AniLibria", "1080"),
        ("AniLibria", "720"),
    ]
