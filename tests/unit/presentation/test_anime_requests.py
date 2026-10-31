from __future__ import annotations

from urllib.parse import quote

from starlette.requests import Request

from backend.application.policies import CatalogLimitsPolicy
from backend.domain.value_objects.anime.genre_filter import GenreMatchMode
from backend.presentation.api.requests.anime_requests import (
    build_autocomplete_anime_query,
    build_filter_anime_catalog_query,
    build_get_season_popular_query,
    build_search_anime_by_description_query,
    build_search_anime_query,
)

POLICY = CatalogLimitsPolicy(
    query_limit_max=50,
    autocomplete_limit_max=20,
    title_max_length=10,
    description_max_length=20,
    genre_hint_max_length=6,
)


def _request(query: str) -> Request:
    """Собрать GET-запрос с переданной строкой параметров."""
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/anime/api/catalog",
            "raw_path": b"/anime/api/catalog",
            "query_string": query.encode("utf-8"),
            "headers": [(b"host", b"testserver")],
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("127.0.0.1", 5000),
        }
    )


def test_search_query_truncates_title_and_clamps_limit() -> None:
    """Что тестируем: сборку запроса поиска из параметров строки запроса.
    Что передаём: длинное название и завышенный limit.
    Что ожидаем: название обрезано по политике, limit ограничен максимумом.
    """
    query = build_search_anime_query(_request("title=1234567890abcdef&limit=500"), POLICY)

    assert query.title == "1234567890"
    assert query.limit == POLICY.query_limit_max
    assert query.include_adult is False


def test_search_query_rejects_unparsable_limit() -> None:
    """Что тестируем: разбор недопустимого limit.
    Что передаём: limit=abc и include_adult=on.
    Что ожидаем: лимит по умолчанию, флаг 18+ распознан.
    """
    query = build_search_anime_query(_request("title=Gintama&limit=abc&include_adult=on"), POLICY)

    assert query.title == "Gintama"
    assert query.limit == 10
    assert query.include_adult is True


def test_autocomplete_query_uses_autocomplete_ceiling() -> None:
    """Что тестируем: потолок выборки для автодополнения.
    Что передаём: limit=1000.
    Что ожидаем: limit ограничен максимумом автодополнения политики.
    """
    query = build_autocomplete_anime_query(_request("query=gina&limit=1000"), POLICY)

    assert query.query == "gina"
    assert query.limit == POLICY.autocomplete_limit_max


def test_season_query_defaults_to_blank_season() -> None:
    """Что тестируем: сборку запроса популярного за сезон.
    Что передаём: пустой сезон и нечисловой год.
    Что ожидаем: сезон пустая строка, год ноль — сценарий подставит текущие.
    """
    query = build_get_season_popular_query(_request("season=&year=abc"), POLICY)

    assert query.season == ""
    assert query.year == 0
    assert query.limit == 10


def test_description_query_trims_limits_and_flags() -> None:
    """Что тестируем: сборку запроса семантического поиска.
    Что передаём: описание и подсказку жанра длиннее лимитов, год и рейтинг.
    Что ожидаем: строки обрезаны по политике, числовые параметры разобраны.
    """
    request = _request(
        "description="
        + quote("очень длинное описание тайтла про самураев")
        + "&genre_hint="
        + quote("Samurai Action")
        + "&year_from=2001&year_to=2010&rating=8&adult_confirmed=1&sort=year"
    )

    query = build_search_anime_by_description_query(request, POLICY)

    assert query.description == "очень длинное описан"
    assert query.genre_hint == "Samura"
    assert query.year_from == 2001
    assert query.year_to == 2010
    assert query.min_rating == 8
    assert query.adult_confirmed is True
    assert query.sort_by == "year"


def test_catalog_query_defaults() -> None:
    """Что тестируем: значения запроса каталога по умолчанию.
    Что передаём: пустую строку параметров.
    Что ожидаем: первая страница, размер по умолчанию, режим «все жанры».
    """
    query = build_filter_anime_catalog_query(_request(""))

    assert query.page == 1
    assert query.per_page == 25
    assert query.genres == ()
    assert query.genre_mode is GenreMatchMode.ALL
    assert query.has_dub is None
    assert query.year_from is None
    assert query.min_score is None
    assert query.sort == "rating"
    assert query.order == "desc"


def test_catalog_query_parses_repeated_and_joined_genres() -> None:
    """Что тестируем: сбор жанров из повторяющихся и слитных параметров.
    Что передаём: genre=Action&genre=Comedy,Drama и genre_mode=any.
    Что ожидаем: уникальные жанры в порядке запроса, режим «любой жанр».
    """
    query = build_filter_anime_catalog_query(
        _request("genre=Action&genre=Comedy,Drama&genre=Action&genre_mode=any")
    )

    assert query.genres == ("Action", "Comedy", "Drama")
    assert query.genre_mode is GenreMatchMode.ANY


def test_catalog_year_and_score_are_clamped() -> None:
    """Что тестируем: ограничение года и рейтинга допустимыми границами.
    Что передаём: год 1800 и min_score 42.
    Что ожидаем: год поднят до нижней границы, рейтинг сведён к десяти.
    """
    query = build_filter_anime_catalog_query(_request("year_from=1800&min_score=42"))

    assert query.year_from == 1950
    assert query.min_score == 10.0


def test_catalog_per_page_snaps_to_nearest_option() -> None:
    """Что тестируем: приведение размера страницы к ближайшему разрешённому.
    Что передаём: per_page=30 и per_page=not-a-number.
    Что ожидаем: 25 в обоих случаях.
    """
    snapped = build_filter_anime_catalog_query(_request("per_page=30"))
    fallback = build_filter_anime_catalog_query(_request("per_page=abc"))

    assert snapped.per_page == 25
    assert fallback.per_page == 25
