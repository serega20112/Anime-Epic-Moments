from __future__ import annotations

from backend.domain import Favorite


def test_favorite_sets_defaults_for_timestamp_and_genres():
    """Проверяем, что Favorite создает added_at и пустой список жанров по умолчанию."""
    favorite = Favorite(user_id=1, anime_id=10)

    assert favorite.added_at is not None
    assert favorite.genres == []


def test_favorite_preserves_snapshot_fields():
    """Проверяем, что Favorite хранит snapshot-поля карточки избранного."""
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
