from __future__ import annotations

import pytest

from backend.domain.anime.entity import Anime


class TestAnimeEntity:
    """Юнит-тесты сущности Anime."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("initial_genres", "genre", "expected"),
        [
            ([], "Comedy", ["Comedy"]),
            (["Comedy"], "Comedy", ["Comedy"]),
        ],
    )
    def test_anime_add_genre_avoids_duplicates(
        self, anime_factory, initial_genres, genre, expected
    ):
        """Что тестируем: поведение метода add_genre.

        Что передаём: начальный список жанров и новый жанр (включая дубликат уже имеющегося).
        Что ожидаем: жанр добавляется один раз, а повторное добавление не создаёт дубликат.
        """
        anime = anime_factory(external_id="1", title="Title", genres=list(initial_genres))

        anime.add_genre(genre)

        assert anime.genres == expected

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("initial_genres", "genre", "expected"),
        [
            (["Comedy", "Drama"], "Comedy", ["Drama"]),
            (["Drama"], "Comedy", ["Drama"]),
        ],
    )
    def test_anime_remove_genre_is_safe(self, anime_factory, initial_genres, genre, expected):
        """Что тестируем: поведение метода remove_genre.

        Что передаём: начальный список жанров и удаляемый жанр (существующий или отсутствующий).
        Что ожидаем: существующий жанр удаляется, отсутствующий просто игнорируется.
        """
        anime = anime_factory(external_id="2", title="Title", genres=list(initial_genres))

        anime.remove_genre(genre)

        assert anime.genres == expected

    @pytest.mark.unit
    def test_anime_constructor_uses_empty_genre_list_by_default(self):
        """Что тестируем: конструктор Anime при отсутствии списка жанров.

        Что передаём: только external_id и title без параметра genres.
        Что ожидаем: атрибут genres становится пустым списком.
        """
        anime = Anime(external_id="3", title="Title", genres=None)

        assert anime.genres == []
