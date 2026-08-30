"""Build application-layer query DTOs from incoming HTTP requests."""

from __future__ import annotations

from fastapi import Request

from backend.application.dto.anime import (
    AutocompleteAnimeQuery,
    FilterAnimeCatalogQuery,
    GetSeasonPopularQuery,
    SearchAnimeByDescriptionQuery,
    SearchAnimeQuery,
)
from backend.config import Settings


async def _to_int(value) -> int | None:
    """Parse an integer query parameter.

    Args:
        value: Raw query parameter value.

    Returns:
        int | None: Parsed integer or None if invalid.
    """
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


async def _to_bool(value) -> bool:
    """Parse a boolean query parameter.

    Args:
        value: Raw query parameter value.

    Returns:
        bool: Parsed boolean.
    """
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


async def _to_float(value) -> float | None:
    """Parse a float query parameter.

    Args:
        value: Raw query parameter value.

    Returns:
        float | None: Parsed float when valid, else None.
    """
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def _clamp_int(value, *, default: int, minimum: int, maximum: int) -> int:
    """Parse and clamp an integer query parameter.

    Args:
        value: Raw query parameter value.
        default: Value used when the parameter is missing or invalid.
        minimum: Minimum allowed value.
        maximum: Maximum allowed value.

    Returns:
        int: Clamped integer value.
    """
    parsed = await _to_int(value)
    if parsed is None:
        return default
    return max(min(parsed, maximum), minimum)


async def build_search_anime_query(request: Request) -> SearchAnimeQuery:
    """Build a search anime query from request parameters.

    Args:
        request: Incoming HTTP request.

    Returns:
        SearchAnimeQuery: Validated query DTO.
    """
    title = str(request.query_params.get("title", "")).strip()[: Settings.anime_title_max_length]
    limit = await _clamp_int(
        request.query_params.get("limit"),
        default=10,
        minimum=1,
        maximum=Settings.anime_query_limit_max,
    )
    include_adult = str(request.query_params.get("include_adult", "")).lower() in (
        "1",
        "true",
        "yes",
    )
    return SearchAnimeQuery(title=title, limit=limit, include_adult=include_adult)


async def build_search_anime_by_description_query(
    request: Request,
) -> SearchAnimeByDescriptionQuery:
    """Build a search by description query from request parameters.

    Args:
        request: Incoming HTTP request.

    Returns:
        SearchAnimeByDescriptionQuery: Validated query DTO.
    """
    description = str(request.query_params.get("description", "")).strip()[
        : Settings.anime_description_max_length
    ]
    genre_hint_raw = str(request.query_params.get("genre_hint", "")).strip()
    genre_hint = genre_hint_raw[: Settings.anime_genre_hint_max_length] or None
    limit = await _clamp_int(
        request.query_params.get("limit"),
        default=10,
        minimum=1,
        maximum=Settings.anime_query_limit_max,
    )
    return SearchAnimeByDescriptionQuery(
        description=description,
        genre_hint=genre_hint,
        limit=limit,
        sort_by=str(request.query_params.get("sort", "match")),
        age_rating=str(request.query_params.get("age_rating", "all")),
        adult_confirmed=await _to_bool(request.query_params.get("adult_confirmed")),
        year_from=await _to_int(request.query_params.get("year_from")),
        year_to=await _to_int(request.query_params.get("year_to")),
        min_rating=await _to_int(request.query_params.get("rating")),
    )


async def build_autocomplete_anime_query(request: Request) -> AutocompleteAnimeQuery:
    """Build an autocomplete query from request parameters.

    Args:
        request: Incoming HTTP request.

    Returns:
        AutocompleteAnimeQuery: Validated query DTO.
    """
    query = str(request.query_params.get("query", "")).strip()[: Settings.anime_title_max_length]
    limit = await _clamp_int(
        request.query_params.get("limit"),
        default=5,
        minimum=1,
        maximum=Settings.anime_autocomplete_limit_max,
    )
    include_adult = str(request.query_params.get("include_adult", "")).lower() in (
        "1",
        "true",
        "yes",
    )
    return AutocompleteAnimeQuery(query=query, limit=limit, include_adult=include_adult)


async def build_get_season_popular_query(request: Request) -> GetSeasonPopularQuery:
    """Build a season popular query from request parameters.

    Args:
        request: Incoming HTTP request.

    Returns:
        GetSeasonPopularQuery: Validated query DTO.
    """
    limit = await _clamp_int(
        request.query_params.get("limit"),
        default=10,
        minimum=1,
        maximum=Settings.anime_query_limit_max,
    )
    return GetSeasonPopularQuery(
        year=await _to_int(request.query_params.get("year")) or 0,
        season=str(request.query_params.get("season") or "").strip(),
        limit=limit,
    )


async def build_filter_anime_catalog_query(request: Request) -> FilterAnimeCatalogQuery:
    """Build an anime catalog filter query from request parameters.

    Args:
        request: Incoming HTTP request.

    Returns:
        FilterAnimeCatalogQuery: Validated query DTO.
    """
    limit = await _clamp_int(
        request.query_params.get("limit"),
        default=30,
        minimum=1,
        maximum=Settings.anime_query_limit_max,
    )
    min_score = await _to_float(request.query_params.get("min_score"))
    if min_score is not None:
        min_score = max(0.0, min(min_score, 10.0))
    return FilterAnimeCatalogQuery(
        genre=str(request.query_params.get("genre", "")).strip()[
            : Settings.anime_genre_hint_max_length
        ],
        media_type=str(request.query_params.get("type", "")).strip().lower(),
        status=str(request.query_params.get("status", "")).strip().lower(),
        year_from=await _clamp_int(
            request.query_params.get("year_from"), default=0, minimum=1950, maximum=2100
        )
        or None,
        year_to=await _clamp_int(
            request.query_params.get("year_to"), default=0, minimum=1950, maximum=2100
        )
        or None,
        min_score=min_score,
        sort=str(request.query_params.get("sort", "rating")).strip(),
        order=str(request.query_params.get("order", "desc")).strip().lower(),
        limit=limit,
    )
