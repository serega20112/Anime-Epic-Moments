from __future__ import annotations

import pytest

from backend.infrastructure.external import AniLibriaClient


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("//cdn.example.com/master.m3u8", "https://cdn.example.com/master.m3u8"),
        ("/videos/master.m3u8", "https://anilibria.top/videos/master.m3u8"),
        ("https://cdn.example.com/master.m3u8", "https://cdn.example.com/master.m3u8"),
    ],
)
def test_anilibria_client_normalizes_links(value, expected):
    """Проверяем, что AniLibriaClient нормализует protocol-relative и root-relative ссылки."""
    assert AniLibriaClient()._normalize_link(value) == expected


def test_anilibria_client_checks_release_relevance_by_title_and_year():
    """Проверяем, что AniLibriaClient отбрасывает нерелевантные релизы по названию и году."""
    client = AniLibriaClient()

    assert client._looks_relevant(
        release={"year": 2024, "name": {"main": "Gintama"}, "alias": "gintama"},
        requested_title="Gintama",
        requested_year=2024,
    ) is True
    assert client._looks_relevant(
        release={"year": 2020, "name": {"main": "Other Title"}, "alias": "other"},
        requested_title="Gintama",
        requested_year=2024,
    ) is False


def test_anilibria_client_maps_release_to_discovered_sources(monkeypatch):
    """Проверяем, что AniLibriaClient собирает источники эпизода по данным релиза и эпизода."""
    client = AniLibriaClient()
    monkeypatch.setattr(
        client,
        "_search_releases",
        lambda title, limit: [
            {
                "id": 77,
                "year": 2024,
                "name": {"main": "Gintama"},
                "alias": "gintama-release",
            }
        ],
    )
    monkeypatch.setattr(
        client,
        "_get_release_details",
        lambda release_id: {
            "episodes": [
                {
                    "ordinal": 2,
                    "hls_1080": "//cdn.example.com/1080.m3u8",
                    "hls_720": "/videos/720.m3u8",
                    "hls_480": None,
                }
            ]
        },
    )

    items = client.search_sources(title="Gintama", episode=2, year=2024)

    assert [(item.quality_label, item.stream_url) for item in items] == [
        ("1080", "https://cdn.example.com/1080.m3u8"),
        ("720", "https://anilibria.top/videos/720.m3u8"),
    ]
