"""Build application-layer query DTOs from incoming HTTP requests."""

from __future__ import annotations

from fastapi import Request

from backend.application.dto.anime_queries import (
    AutocompleteAnimeQuery,
    GetSeasonPopularQuery,
    SearchAnimeByDescriptionQuery,
    SearchAnimeQuery,
)
from backend.config import Settings


def _to_int(value) -> int | None:
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


def _to_bool(value) -> bool:
    """Parse a boolean query parameter.

    Args:
        value: Raw query parameter value.

    Returns:
        bool: Parsed boolean.
    """
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _clamp_int(value, *, default: int, minimum: int, maximum: int) -> int:
    """Parse and clamp an integer query parameter.

    Args:
        value: Raw query parameter value.
        default: Value used when the parameter is missing or invalid.
        minimum: Minimum allowed value.
        maximum: Maximum allowed value.

    Returns:
        int: Clamped integer value.
    """
    parsed = _to_int(value)
    if parsed is None:
        return default
    return max(min(parsed, maximum), minimum)


def build_search_anime_query(request: Request) -> SearchAnimeQuery:
    """Build a search anime query from request parameters.

    Args:
        request: Incoming HTTP request.

    Returns:
        SearchAnimeQuery: Validated query DTO.
    """
    title = str(request.query_params.get("title", "")).strip()[
        : Settings.anime_title_max_length
    ]
    limit = _clamp_int(
        request.query_params.get("limit"),
        default=10,
        minimum=1,
        maximum=Settings.anime_query_limit_max,
    )
    return SearchAnimeQuery(title=title, limit=limit)


def build_search_anime_by_description_query(
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
    limit = _clamp_int(
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
        adult_confirmed=_to_bool(request.query_params.get("adult_confirmed")),
        year_from=_to_int(request.query_params.get("year_from")),
        year_to=_to_int(request.query_params.get("year_to")),
        min_rating=_to_int(request.query_params.get("rating")),
    )


def build_autocomplete_anime_query(request: Request) -> AutocompleteAnimeQuery:
    """Build an autocomplete query from request parameters.

    Args:
        request: Incoming HTTP request.

    Returns:
        AutocompleteAnimeQuery: Validated query DTO.
    """
    query = str(request.query_params.get("query", "")).strip()[
        : Settings.anime_title_max_length
    ]
    limit = _clamp_int(
        request.query_params.get("limit"),
        default=5,
        minimum=1,
        maximum=Settings.anime_autocomplete_limit_max,
    )
    return AutocompleteAnimeQuery(query=query, limit=limit)


def build_get_season_popular_query(request: Request) -> GetSeasonPopularQuery:
    """Build a season popular query from request parameters.

    Args:
        request: Incoming HTTP request.

    Returns:
        GetSeasonPopularQuery: Validated query DTO.
    """
    limit = _clamp_int(
        request.query_params.get("limit"),
        default=10,
        minimum=1,
        maximum=Settings.anime_query_limit_max,
    )
    return GetSeasonPopularQuery(
        year=_to_int(request.query_params.get("year")) or 0,
        season=str(request.query_params.get("season") or "").strip(),
        limit=limit,
    )
