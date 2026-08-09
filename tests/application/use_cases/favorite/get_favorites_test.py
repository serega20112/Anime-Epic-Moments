from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.application.use_cases import GetFavoritesUseCase


@pytest.mark.parametrize(
    ("favorite_payload", "expected_title", "expected_watch_url", "expected_calls"),
    [
        (
                {
                    "anime_id": 185,
                    "title": "Initial D First Stage",
                    "description": "desc",
                    "cover_url": "cover",
                    "genres": ["Action"],
                },
                "Initial D First Stage",
                "/watch/185?episode=1",
                0,
        ),
        (
                {
                    "anime_id": 19613,
                    "title": None,
                    "description": None,
                    "cover_url": None,
                    "genres": [],
                },
                "New Initial D Movie: Legend 1 - Kakusei",
                "/watch/22507?episode=1",
                1,
        ),
    ],
)
def test_get_favorites_use_case_prefers_snapshot_and_falls_back_to_api(
        favorite_payload,
        expected_title,
        expected_watch_url,
        expected_calls,
        anime_factory,
):
    """Проверяем, что favorites берут snapshot из БД и только при необходимости идут во внешний API."""
    repo = Mock()
    repo.get_by_user.return_value = [
        SimpleNamespace(
            user_id=1,
            anime_id=favorite_payload["anime_id"],
            title=favorite_payload["title"],
            description=favorite_payload["description"],
            cover_url=favorite_payload["cover_url"],
            genres=favorite_payload["genres"],
            added_at=datetime(2026, 3, 28),
        )
    ]
    anime_client = Mock()
    anime_client.get_by_id.return_value = anime_factory(
        external_id="22507",
        title="New Initial D Movie: Legend 1 - Kakusei",
        genres=["Action"],
    )
    use_case = GetFavoritesUseCase(repo, anime_client)

    result = use_case.execute(user_id=1)

    assert result[0].title == expected_title
    assert result[0].watch_url == expected_watch_url
    assert anime_client.get_by_id.call_count == expected_calls
