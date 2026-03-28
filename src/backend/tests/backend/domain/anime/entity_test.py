from __future__ import annotations

import pytest

from src.backend.domain.anime.entity import Anime


@pytest.mark.parametrize(
    ("initial_genres", "genre", "expected"),
    [
        ([], "Comedy", ["Comedy"]),
        (["Comedy"], "Comedy", ["Comedy"]),
    ],
)
def test_anime_add_genre_avoids_duplicates(initial_genres, genre, expected):
    """Проверяем, что add_genre добавляет жанр один раз и не дублирует его."""
    anime = Anime(external_id="1", title="Title", genres=list(initial_genres))

    anime.add_genre(genre)

    assert anime.genres == expected


@pytest.mark.parametrize(
    ("initial_genres", "genre", "expected"),
    [
        (["Comedy", "Drama"], "Comedy", ["Drama"]),
        (["Drama"], "Comedy", ["Drama"]),
    ],
)
def test_anime_remove_genre_is_safe(initial_genres, genre, expected):
    """Проверяем, что remove_genre удаляет существующий жанр и игнорирует отсутствующий."""
    anime = Anime(external_id="2", title="Title", genres=list(initial_genres))

    anime.remove_genre(genre)

    assert anime.genres == expected


def test_anime_constructor_uses_empty_genre_list_by_default():
    """Проверяем, что Anime создает пустой список жанров, если они не переданы."""
    anime = Anime(external_id="3", title="Title", genres=None)

    assert anime.genres == []
