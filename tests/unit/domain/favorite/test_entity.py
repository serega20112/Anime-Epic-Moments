from __future__ import annotations

import pytest

from backend.domain.favorite.entity import Favorite


class TestFavorite:
    """Юнит-тесты сущности Favorite."""

    @pytest.mark.unit
    def test_sets_defaults_for_timestamp_and_genres(self):
        """Что тестируем: конструктор Favorite при минимальном наборе полей.

        Что передаём: только user_id и anime_id без timestamp и жанров.
        Что ожидаем: added_at заполнен, genres становится пустым списком.
        """
        favorite = Favorite(user_id=1, anime_id=10)

        assert favorite.added_at is not None
        assert favorite.genres == []

    @pytest.mark.unit
    def test_preserves_snapshot_fields(self):
        """Что тестируем: конструктор Favorite при передаче snapshot-полей.

        Что передаём: карточку избранного с названием, описанием, обложкой и жанрами.
        Что ожидаем: все snapshot-поля сохраняются корректно.
        """
        favorite = Favorite(
            user_id=1,
            anime_id=10,
            title="Initial D",
            description="Street racing",
            cover_url="https://example.com/initial-d.jpg",
            genres=["Action", "Cars"],
        )

        assert favorite.title == "Initial D"
        assert favorite.description == "Street racing"
        assert favorite.cover_url == "https://example.com/initial-d.jpg"
        assert favorite.genres == ["Action", "Cars"]
