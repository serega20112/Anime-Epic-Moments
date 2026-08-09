from __future__ import annotations

import pytest

from backend.infrastructure.external import YouTubeClient


def test_youtube_client_builds_unique_queries():
    """Проверяем, что YouTubeClient формирует уникальные запросы для эпизода и года."""
    client = YouTubeClient()

    queries = client._build_queries(title="Gintama", episode=2, year=2024)

    assert queries == ['"Gintama" 2 серия', '"Gintama" episode 2', '"Gintama" 2024 2 серия']


@pytest.mark.parametrize(
    ("title", "channel", "expected_positive"),
    [
        ("Gintama 2 серия AniLibria", "AniLibria", True),
        ("Gintama trailer", "AniLibria", False),
    ],
)
def test_youtube_client_scores_relevant_videos(title, channel, expected_positive):
    """Проверяем, что YouTubeClient отличает релевантный эпизод от трейлеров и нерелевантного видео."""
    client = YouTubeClient()

    score = client._score_video(
        video_title=title,
        channel_title=channel,
        requested_title="Gintama",
        requested_episode=2,
    )

    assert (score > 0) is expected_positive


def test_youtube_client_search_sources_deduplicates_and_sorts(monkeypatch):
    """Проверяем, что YouTubeClient убирает дубликаты между запросами и сортирует найденные видео."""
    client = YouTubeClient()
    client.api_key = "token"
    monkeypatch.setattr(client, "_build_queries", lambda title, episode, year: ["q1", "q2"])
    monkeypatch.setattr(
        client,
        "_search_videos",
        lambda query, limit: [
            {
                "id": {"videoId": "abc"},
                "snippet": {
                    "title": "Gintama 2 серия AniLibria",
                    "channelTitle": "AniLibria",
                },
            },
            {
                "id": {"videoId": "def"},
                "snippet": {
                    "title": "Gintama episode 2 subtitles",
                    "channelTitle": "Fansub Team",
                },
            },
        ],
    )

    items = client.search_sources(title="Gintama", episode=2, limit=5)

    assert len(items) == 2
    assert items[0].stream_url.endswith("/abc?enablejsapi=1&rel=0&modestbranding=1")
    assert {item.translation_type for item in items} == {"voice", "sub"}
