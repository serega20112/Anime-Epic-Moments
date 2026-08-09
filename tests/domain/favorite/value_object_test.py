from __future__ import annotations

from dataclasses import asdict

from backend.domain.favorite import FavoriteAnimeCard


def test_favorite_anime_card_exposes_expected_fields():
    """Проверяем, что FavoriteAnimeCard хранит все данные карточки избранного."""
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
