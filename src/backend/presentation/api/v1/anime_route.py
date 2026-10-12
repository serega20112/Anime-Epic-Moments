"""Thin HTTP routes for anime search and discovery."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.use_cases import GetSeasonPopularUseCase, SearchAnimeUseCase
from backend.application.use_cases.anime.autocomplete_anime import AutocompleteAnimeUseCase
from backend.application.use_cases.anime.filter_anime_catalog import FilterAnimeCatalogUseCase
from backend.application.use_cases.anime.search_anime_by_description import (
    SearchAnimeByDescriptionUseCase,
)
from backend.infrastructure.security.flask_protection import client_ip, rate_limit
from backend.infrastructure.web import render_template
from backend.presentation.api.requests.anime_requests import (
    CATALOG_PER_PAGE_OPTIONS,
    build_autocomplete_anime_query,
    build_filter_anime_catalog_query,
    build_get_season_popular_query,
    build_search_anime_by_description_query,
    build_search_anime_query,
)

anime_router = APIRouter(prefix="/anime", route_class=DishkaRoute)
anime_bp = anime_router


@anime_router.get("/search", name="anime.search_anime_page")
async def search_anime_page(request: Request):
    """Render the anime search page.

    Args:
        request: Incoming HTTP request.

    Returns:
        HTMLResponse: Rendered search page.
    """
    return await render_template(
        request,
        "anime/search.html",
        initial_title=request.query_params.get("title", ""),
    )


@anime_router.get("/search/description", name="anime.search_by_description_page")
async def search_by_description_page(request: Request):
    """Render the search by description page.

    Args:
        request: Incoming HTTP request.

    Returns:
        HTMLResponse: Rendered search page.
    """
    return await render_template(request, "anime/search_by_description.html")


@anime_router.get("/catalog", name="anime.catalog_page")
async def catalog_page(request: Request):
    """Render the filterable anime catalog page.

    Args:
        request: Incoming HTTP request.

    Returns:
        HTMLResponse: Rendered catalog page.
    """
    params = request.query_params
    return await render_template(
        request,
        "anime/catalog.html",
        initial_filters={
            "genres": params.getlist("genre"),
            "genre_mode": params.get("genre_mode", ""),
            "type": params.get("type", ""),
            "status": params.get("status", ""),
            "min_score": params.get("min_score", ""),
            "year_from": params.get("year_from", ""),
            "year_to": params.get("year_to", ""),
            "sort": params.get("sort", ""),
            "has_dub": params.get("has_dub", ""),
            "page": params.get("page", ""),
            "per_page": params.get("per_page", ""),
        },
        per_page_options=list(CATALOG_PER_PAGE_OPTIONS),
    )


@anime_router.get("/api/search", name="anime.search_anime")
@rate_limit(
    scope="anime_search",
    limit=60,
    window_seconds=60,
    key_builder=lambda request: client_ip(request),
)
async def search_anime(
    request: Request,
    use_case: FromDishka[SearchAnimeUseCase],
):
    """Search anime by title.

    Args:
        request: Incoming HTTP request.
        use_case: Search anime use case.

    Returns:
        list[dict]: List of anime dictionaries.
    """
    query = await build_search_anime_query(request)
    results = await use_case.execute(query)
    return [vars(anime) for anime in results]


@anime_router.get("/api/search/description", name="anime.search_anime_by_description")
@rate_limit(
    scope="anime_search_description",
    limit=30,
    window_seconds=60,
    key_builder=lambda request: client_ip(request),
)
async def search_anime_by_description(
    request: Request,
    use_case: FromDishka[SearchAnimeByDescriptionUseCase],
):
    """Search anime by natural language description.

    Args:
        request: Incoming HTTP request.
        use_case: Search by description use case.

    Returns:
        dict: Search result payload.
    """
    query = await build_search_anime_by_description_query(request)
    result = await use_case.execute(query)
    return result.to_dict()


@anime_router.get("/api/autocomplete", name="anime.autocomplete_anime")
@rate_limit(
    scope="anime_autocomplete",
    limit=90,
    window_seconds=60,
    key_builder=lambda request: client_ip(request),
)
async def autocomplete_anime(
    request: Request,
    use_case: FromDishka[AutocompleteAnimeUseCase],
):
    """Autocomplete anime titles.

    Args:
        request: Incoming HTTP request.
        use_case: Autocomplete use case.

    Returns:
        list[dict]: List of anime suggestions.
    """
    query = await build_autocomplete_anime_query(request)
    suggestions = await use_case.execute(query)
    return [vars(anime) for anime in suggestions]


@anime_router.get("/api/catalog", name="anime.filter_anime_catalog")
@rate_limit(
    scope="anime_catalog",
    limit=60,
    window_seconds=60,
    key_builder=lambda request: client_ip(request),
)
async def filter_anime_catalog(
    request: Request,
    use_case: FromDishka[FilterAnimeCatalogUseCase],
):
    """Browse anime with Anixart-style filters.

    Args:
        request: Incoming HTTP request.
        use_case: Catalog filter use case.

    Returns:
        dict[str, object]: Requested page of anime together with pagination
            metadata and the genre facets found in the results.
    """
    query = await build_filter_anime_catalog_query(request)
    result = await use_case.execute(query)
    return result.to_dict()


@anime_router.get("/api/season/popular", name="anime.get_season_popular")
@rate_limit(
    scope="anime_season_popular",
    limit=60,
    window_seconds=60,
    key_builder=lambda request: client_ip(request),
)
async def get_season_popular(
    request: Request,
    use_case: FromDishka[GetSeasonPopularUseCase],
):
    """Fetch popular anime for a season.

    Args:
        request: Incoming HTTP request.
        use_case: Season popular use case.

    Returns:
        list[dict]: List of anime dictionaries.
    """
    query = await build_get_season_popular_query(request)
    results = await use_case.execute(query)
    return [vars(anime) for anime in results]
