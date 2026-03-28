from __future__ import annotations

import pytest

from src.backend.domain.anime.entity import Anime
from src.backend.domain.anime.policy import AnimeSafetyPolicy


@pytest.mark.parametrize(
    ("description", "genre_hint", "expected"),
    [
        ("ищу смешной сериал", None, False),
        ("ищу hentai comedy", None, True),
        ("романтика", "ecchi", True),
    ],
)
def test_has_explicit_adult_intent_detects_explicit_queries(
    description,
    genre_hint,
    expected,
):
    """Проверяем, что policy различает обычный и явно взрослый запрос."""
    result = AnimeSafetyPolicy.has_explicit_adult_intent(description, genre_hint)

    assert result is expected


@pytest.mark.parametrize(
    ("title", "description", "genres", "expected"),
    [
        ("Normal Title", "funny school story", ["Comedy"], False),
        ("Ecchi Show", "funny school story", ["Comedy"], True),
        ("Normal Title", "explicit romance", ["Drama"], True),
    ],
)
def test_is_probably_nsfw_uses_title_description_and_genres(
    title,
    description,
    genres,
    expected,
):
    """Проверяем, что policy отмечает NSFW по заголовку, описанию и жанрам карточки."""
    anime = Anime(external_id="11", title=title, description=description, genres=genres)

    assert AnimeSafetyPolicy.is_probably_nsfw(anime) is expected


def test_suggest_title_hints_extracts_unique_quoted_titles():
    """Проверяем, что suggest_title_hints извлекает уникальные названия из кавычек."""
    result = AnimeSafetyPolicy.suggest_title_hints(
        'хочу что-то как "Gintama" и «KonoSuba», но не "Gintama"',
        genre_hint="'Saiki Kusuo no Psi-nan'",
    )

    assert result == ["Gintama", "KonoSuba", "Saiki Kusuo no Psi-nan"]
