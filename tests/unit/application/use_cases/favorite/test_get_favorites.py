from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.favorite.get_favorites import GetFavoritesUseCase


@pytest.mark.unit
class TestGetFavoritesUseCase:
    """Юнит-тесты сценария получения списка favorites."""

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
                    "original_title": "Initial D",
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
                    "original_title": None,
                },
                "New Initial D Movie: Legend 1 - Kakusei",
                "/watch/22507?episode=1",
                1,
            ),
        ],
    )
    async def test_prefers_snapshot_and_falls_back_to_api(
        self,
        favorite_payload,
        expected_title,
        expected_watch_url,
        expected_calls,
        anime_factory,
    ):
        """Что тестируем: favorites берут snapshot из БД и только при необходимости идут в API.
        Что передаём: favorite с заполненными/пустыми snapshot-полями.
        Что ожидаем: title и watch_url подобраны, get_by_id вызывается только при пустом title.
        """
        repo = AsyncMock()
        repo.get_by_user.return_value = [
            SimpleNamespace(
                user_id=1,
                anime_id=favorite_payload["anime_id"],
                title=favorite_payload["title"],
                description=favorite_payload["description"],
                cover_url=favorite_payload["cover_url"],
                genres=favorite_payload["genres"],
                original_title=favorite_payload["original_title"],
                added_at=datetime(2026, 3, 28),
            )
        ]
        anime_client = AsyncMock()
        anime_client.get_by_id.return_value = anime_factory(
            external_id="22507",
            title="New Initial D Movie: Legend 1 - Kakusei",
            genres=["Action"],
        )
        use_case = GetFavoritesUseCase(repo, anime_client)

        result = await use_case.execute(user_id=1)

        assert result[0].title == expected_title
        assert result[0].watch_url == expected_watch_url
        assert anime_client.get_by_id.await_count == expected_calls

    async def test_uses_fallback_title_when_api_returns_anime_without_title(self):
        """Что тестируем: fallback-название, когда источник не вернул title.
        Что передаём: favorite без title и anime из API.
        Что ожидаем: используются название и описание из API или заглушка.
        """
        repo = AsyncMock()
        repo.get_by_user.return_value = [
            SimpleNamespace(
                user_id=1,
                anime_id=777,
                title=None,
                description=None,
                cover_url="cover",
                genres=[],
                original_title=None,
                added_at=datetime(2026, 3, 28),
            )
        ]
        anime_client = AsyncMock()
        anime_client.get_by_id.return_value = SimpleNamespace(
            external_id=None,
            title=None,
            description=None,
            cover_url=None,
            genres=[],
            original_title=None,
        )
        use_case = GetFavoritesUseCase(repo, anime_client)

        result = await use_case.execute(user_id=1)

        assert result[0].title == "Anime #777"
        assert result[0].description == "Описание недоступно"
        assert result[0].watch_url == "/watch/777?episode=1"
