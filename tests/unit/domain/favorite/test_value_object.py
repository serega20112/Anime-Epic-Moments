from __future__ import annotations

from dataclasses import asdict

import pytest

from backend.domain.value_objects.favorite.favorite_card import FavoriteAnimeCard


class TestFavoriteAnimeCard:
    """Юнит-тесты value object карточки избранного."""

    @pytest.mark.unit
    def test_exposes_expected_fields(self):
        """Что тестируем: поля FavoriteAnimeCard.

        Что передаём: все данные карточки избранного (id, название, жанры, ссылки).
        Что ожидаем: asdict возвращает корректный словарь всех полей.
        """
        card = FavoriteAnimeCard(
            anime_id=185,
            title="Initial D First Stage",
            description="Street racing",
            cover_url="https://example.com/cover.jpg",
            genres=["Action", "Cars"],
            watch_url="/watch/185",
            added_at="2026-03-28",
        )

        assert asdict(card) == {
            "anime_id": 185,
            "title": "Initial D First Stage",
            "description": "Street racing",
            "cover_url": "https://example.com/cover.jpg",
            "genres": ["Action", "Cars"],
            "watch_url": "/watch/185",
            "added_at": "2026-03-28",
        }
