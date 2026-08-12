from __future__ import annotations

import pytest

from backend.domain.anime.entity import Anime
from backend.domain.anime.policy import AnimeSafetyPolicy


class TestAnimeSafetyPolicy:
    """Юнит-тесты доменной политики безопасности поиска аниме."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("description", "genre_hint", "expected"),
        [
            ("ищу смешной сериал", None, False),
            ("ищу hentai comedy", None, True),
            ("романтика", "ecchi", True),
        ],
    )
    def test_has_explicit_adult_intent_detects_explicit_queries(
            self,
            description,
            genre_hint,
            expected,
    ):
        """Что тестируем: метод has_explicit_adult_intent.

        Что передаём: текст запроса и необязательный жанр-подсказку (в том числе явно взрослые маркеры).
        Что ожидаем: метод различает обычный и явно взрослый запрос, возвращая ожидаемый bool.
        """
        result = AnimeSafetyPolicy.has_explicit_adult_intent(description, genre_hint)

        assert result is expected

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("title", "description", "genres", "expected"),
        [
            ("Normal Title", "funny school story", ["Comedy"], False),
            ("Ecchi Show", "funny school story", ["Comedy"], True),
            ("Normal Title", "explicit romance", ["Drama"], True),
        ],
    )
    def test_is_probably_nsfw_uses_title_description_and_genres(
            self,
            title,
            description,
            genres,
            expected,
    ):
        """Что тестируем: метод is_probably_nsfw.

        Что передаём: сущность Anime с разными заголовком, описанием и жанрами.
        Что ожидаем: NSFW маркеры в любом из полей приводят к True, иначе False.
        """
        anime = Anime(external_id="11", title=title, description=description, genres=genres)

        assert AnimeSafetyPolicy.is_probably_nsfw(anime) is expected

    @pytest.mark.unit
    def test_suggest_title_hints_extracts_unique_quoted_titles(self):
        """Что тестируем: метод suggest_title_hints.

        Что передаём: текст с названиями в разных типах кавычек и повторяющимся «Gintama».
        Что ожидаем: извлекаются уникальные нормализованные названия в порядке появления.
        """
        result = AnimeSafetyPolicy.suggest_title_hints(
            'хочу что-то как "Gintama" и «KonoSuba», но не "Gintama"',
            genre_hint="'Saiki Kusuo no Psi-nan'",
        )

        assert result == ["Gintama", "KonoSuba", "Saiki Kusuo no Psi-nan"]