"""Сборка запросов слоя application из параметров HTTP-запроса."""

from __future__ import annotations

from typing import Any

from fastapi import Request

from backend.application.dto.anime import (
    AutocompleteAnimeQuery,
    FilterAnimeCatalogQuery,
    GetSeasonPopularQuery,
    SearchAnimeByDescriptionQuery,
    SearchAnimeQuery,
)
from backend.application.policies import CatalogLimitsPolicy
from backend.domain.value_objects.anime.genre_filter import GenreMatchMode

CATALOG_PER_PAGE_OPTIONS = (10, 25, 50, 100)
CATALOG_DEFAULT_PER_PAGE = 25
CATALOG_MIN_PER_PAGE = 10
CATALOG_MAX_PER_PAGE = 100
CATALOG_MAX_PAGE = 500
CATALOG_MAX_GENRES = 12
DEFAULT_SEARCH_LIMIT = 10
DEFAULT_AUTOCOMPLETE_LIMIT = 5
MIN_SCORE_FLOOR = 0.0
MIN_SCORE_CEILING = 10.0


def _to_int(value: Any) -> int | None:
    """Разобрать целочисленный параметр запроса.

    Args:
        value: Сырое значение параметра.

    Returns:
        int | None: Разобранное число либо None, если параметр не число.
    """
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> bool:
    """Разобрать булев параметр запроса.

    Args:
        value: Сырое значение параметра.

    Returns:
        bool: True для ``1``, ``true``, ``yes`` и ``on``.
    """
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _to_float(value: Any) -> float | None:
    """Разобрать дробный параметр запроса.

    Args:
        value: Сырое значение параметра.

    Returns:
        float | None: Разобранное число либо None, если параметр не число.
    """
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    """Разобрать целое и ограничить его допустимым диапазоном.

    Args:
        value: Сырое значение параметра.
        default: Значение, если параметра нет или он не число.
        minimum: Нижняя граница диапазона.
        maximum: Верхняя граница диапазона.

    Returns:
        int: Число внутри диапазона.
    """
    parsed = _to_int(value)
    if parsed is None:
        return default
    return max(min(parsed, maximum), minimum)


def _collect_genres(request: Request) -> tuple[str, ...]:
    """Собрать выбранные жанры из повторяющихся или слитных параметров.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        tuple[str, ...]: Уникальные жанры в порядке запроса.
    """
    collected: list[str] = []
    for raw in request.query_params.getlist("genre"):
        for part in str(raw).split(","):
            name = part.strip()
            if name and name not in collected:
                collected.append(name)
    return tuple(collected[:CATALOG_MAX_GENRES])


def build_search_anime_query(request: Request, policy: CatalogLimitsPolicy) -> SearchAnimeQuery:
    """Собрать запрос поиска аниме из параметров запроса.

    Args:
        request: Текущий HTTP-запрос.
        policy: Лимиты строк и выборки каталога.

    Returns:
        SearchAnimeQuery: Проверенный query-объект.
    """
    params = request.query_params
    return SearchAnimeQuery(
        title=str(params.get("title", "")).strip()[: policy.title_max_length],
        limit=_clamp_int(
            params.get("limit"),
            default=DEFAULT_SEARCH_LIMIT,
            minimum=1,
            maximum=policy.query_limit_max,
        ),
        include_adult=_to_bool(params.get("include_adult")),
    )


def build_search_anime_by_description_query(
    request: Request, policy: CatalogLimitsPolicy
) -> SearchAnimeByDescriptionQuery:
    """Собрать запрос поиска по описанию из параметров запроса.

    Args:
        request: Текущий HTTP-запрос.
        policy: Лимиты строк и выборки каталога.

    Returns:
        SearchAnimeByDescriptionQuery: Проверенный query-объект.
    """
    params = request.query_params
    genre_hint = str(params.get("genre_hint", "")).strip()[: policy.genre_hint_max_length]
    return SearchAnimeByDescriptionQuery(
        description=str(params.get("description", "")).strip()[: policy.description_max_length],
        genre_hint=genre_hint or None,
        limit=_clamp_int(
            params.get("limit"),
            default=DEFAULT_SEARCH_LIMIT,
            minimum=1,
            maximum=policy.query_limit_max,
        ),
        sort_by=str(params.get("sort", "match")).strip(),
        age_rating=str(params.get("age_rating", "all")).strip(),
        adult_confirmed=_to_bool(params.get("adult_confirmed")),
        year_from=_to_int(params.get("year_from")),
        year_to=_to_int(params.get("year_to")),
        min_rating=_to_int(params.get("rating")),
    )


def build_autocomplete_anime_query(
    request: Request, policy: CatalogLimitsPolicy
) -> AutocompleteAnimeQuery:
    """Собрать запрос автодополнения из параметров запроса.

    Args:
        request: Текущий HTTP-запрос.
        policy: Лимиты строк и выборки каталога.

    Returns:
        AutocompleteAnimeQuery: Проверенный query-объект.
    """
    params = request.query_params
    return AutocompleteAnimeQuery(
        query=str(params.get("query", "")).strip()[: policy.title_max_length],
        limit=_clamp_int(
            params.get("limit"),
            default=DEFAULT_AUTOCOMPLETE_LIMIT,
            minimum=1,
            maximum=policy.autocomplete_limit_max,
        ),
        include_adult=_to_bool(params.get("include_adult")),
    )


def build_get_season_popular_query(
    request: Request, policy: CatalogLimitsPolicy
) -> GetSeasonPopularQuery:
    """Собрать запрос популярного за сезон из параметров запроса.

    Args:
        request: Текущий HTTP-запрос.
        policy: Лимиты строк и выборки каталога.

    Returns:
        GetSeasonPopularQuery: Проверенный query-объект.
    """
    params = request.query_params
    return GetSeasonPopularQuery(
        year=_to_int(params.get("year")) or 0,
        season=str(params.get("season") or "").strip(),
        limit=_clamp_int(
            params.get("limit"),
            default=DEFAULT_SEARCH_LIMIT,
            minimum=1,
            maximum=policy.query_limit_max,
        ),
    )


def build_filter_anime_catalog_query(request: Request) -> FilterAnimeCatalogQuery:
    """Собрать запрос фильтра каталога из параметров запроса.

    Жанры можно передать повтором (``?genre=Action&genre=Comedy``) или через
    запятую (``?genre=Action,Comedy``): обе формы приводятся к кортежу.
    Параметр ``genre_mode`` решает, нужны ли все выбранные жанры сразу или
    достаточно любого совпадения.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        FilterAnimeCatalogQuery: Проверенный query-объект.
    """
    params = request.query_params
    raw_has_dub = params.get("has_dub")
    return FilterAnimeCatalogQuery(
        genres=_collect_genres(request),
        genre_mode=GenreMatchMode.parse(params.get("genre_mode")),
        media_type=str(params.get("type", "")).strip().lower(),
        status=str(params.get("status", "")).strip().lower(),
        has_dub=None if raw_has_dub in (None, "") else _to_bool(raw_has_dub),
        year_from=_clamp_year(params.get("year_from")),
        year_to=_clamp_year(params.get("year_to")),
        min_score=_clamped_min_score(params.get("min_score")),
        sort=str(params.get("sort", "rating")).strip(),
        order=str(params.get("order", "desc")).strip().lower(),
        page=_clamp_int(params.get("page"), default=1, minimum=1, maximum=CATALOG_MAX_PAGE),
        per_page=_clamp_per_page(params.get("per_page")),
        include_adult=_to_bool(params.get("include_adult")),
    )


def _clamp_year(value: Any) -> int | None:
    """Ограничить год выпуска допустимым диапазоном каталога.

    Args:
        value: Сырое значение параметра года.

    Returns:
        int | None: Год внутри диапазона либо None при отсутствии параметра.
    """
    clamped = _clamp_int(value, default=0, minimum=1950, maximum=2100)
    return clamped or None


def _clamped_min_score(value: Any) -> float | None:
    """Ограничить минимальный рейтинг шкалой каталога.

    Args:
        value: Сырое значение рейтинга.

    Returns:
        float | None: Рейтинг от нуля до десяти либо None при нечислом входе.
    """
    min_score = _to_float(value)
    if min_score is None:
        return None
    return max(MIN_SCORE_FLOOR, min(min_score, MIN_SCORE_CEILING))


def _clamp_per_page(value: Any) -> int:
    """Привести размер страницы к ближайшему разрешённому значению.

    Args:
        value: Сырое значение параметра ``per_page``.

    Returns:
        int: Размер страницы из набора :data:`CATALOG_PER_PAGE_OPTIONS`.
    """
    requested = _clamp_int(
        value,
        default=CATALOG_DEFAULT_PER_PAGE,
        minimum=CATALOG_MIN_PER_PAGE,
        maximum=CATALOG_MAX_PER_PAGE,
    )
    if requested in CATALOG_PER_PAGE_OPTIONS:
        return requested
    return min(CATALOG_PER_PAGE_OPTIONS, key=lambda option: abs(option - requested))
