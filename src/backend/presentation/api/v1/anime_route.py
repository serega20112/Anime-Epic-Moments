"""Тонкие HTTP-маршруты поиска и каталога аниме."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.policies import CatalogLimitsPolicy
from backend.application.use_cases import GetSeasonPopularUseCase, SearchAnimeUseCase
from backend.application.use_cases.anime.autocomplete_anime import AutocompleteAnimeUseCase
from backend.application.use_cases.anime.filter_anime_catalog import FilterAnimeCatalogUseCase
from backend.application.use_cases.anime.search_anime_by_description import (
    SearchAnimeByDescriptionUseCase,
)
from backend.presentation.api.rate_limit import client_ip, rate_limit
from backend.presentation.api.requests.anime_requests import (
    CATALOG_PER_PAGE_OPTIONS,
    build_autocomplete_anime_query,
    build_filter_anime_catalog_query,
    build_get_season_popular_query,
    build_search_anime_by_description_query,
    build_search_anime_query,
)
from backend.presentation.api.responses.anime_responses import (
    AnimeCardResponse,
    AnimeCatalogPage,
    AnimeSearchResultResponse,
)
from backend.presentation.web import render_template

anime_router = APIRouter(prefix="/anime", route_class=DishkaRoute)


@anime_router.get("/search", name="anime.search_anime_page")
async def search_anime_page(request: Request):
    """Отдать страницу поиска аниме."""
    return await render_template(
        request,
        "anime/search.html",
        initial_title=request.query_params.get("title", ""),
    )


@anime_router.get("/search/description", name="anime.search_by_description_page")
async def search_by_description_page(request: Request):
    """Отдать страницу поиска по описанию."""
    return await render_template(request, "anime/search_by_description.html")


@anime_router.get("/catalog", name="anime.catalog_page")
async def catalog_page(request: Request):
    """Отдать страницу каталога с фильтрами."""
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


@anime_router.get("/api/search", name="anime.search_anime", response_model=list[AnimeCardResponse])
@rate_limit(
    scope="anime_search",
    limit=60,
    window_seconds=60,
    key_builder=lambda request: client_ip(request),
)
async def search_anime(
    request: Request,
    use_case: FromDishka[SearchAnimeUseCase],
    policy: FromDishka[CatalogLimitsPolicy],
) -> list:
    """Найти аниме по названию.

    Args:
        request: Текущий HTTP-запрос с параметрами поиска.
        use_case: Сценарий поиска по названию.
        policy: Лимиты строк и выборки каталога.

    Returns:
        list: Найденные тайтлы в представлении каталога.
    """
    return await use_case.execute(build_search_anime_query(request, policy))


@anime_router.get(
    "/api/search/description",
    name="anime.search_anime_by_description",
    response_model=AnimeSearchResultResponse,
)
@rate_limit(
    scope="anime_search_description",
    limit=30,
    window_seconds=60,
    key_builder=lambda request: client_ip(request),
)
async def search_anime_by_description(
    request: Request,
    use_case: FromDishka[SearchAnimeByDescriptionUseCase],
    policy: FromDishka[CatalogLimitsPolicy],
) -> AnimeSearchResultResponse:
    """Найти аниме по описанию на естественном языке.

    Args:
        request: Текущий HTTP-запрос с параметрами описания.
        use_case: Сценарий поиска по описанию.
        policy: Лимиты строк и выборки каталога.

    Returns:
        AnimeSearchResultResponse: Итог поиска с тайтлами и признаком
            необходимости подтверждения возраста.
    """
    query = build_search_anime_by_description_query(request, policy)
    return await use_case.execute(query)


@anime_router.get(
    "/api/autocomplete", name="anime.autocomplete_anime", response_model=list[AnimeCardResponse]
)
@rate_limit(
    scope="anime_autocomplete",
    limit=90,
    window_seconds=60,
    key_builder=lambda request: client_ip(request),
)
async def autocomplete_anime(
    request: Request,
    use_case: FromDishka[AutocompleteAnimeUseCase],
    policy: FromDishka[CatalogLimitsPolicy],
) -> list:
    """Подсказать названия аниме по префиксу.

    Args:
        request: Текущий HTTP-запрос с параметром ``query``.
        use_case: Сценарий автодополнения названий.
        policy: Лимиты строк и выборки каталога.

    Returns:
        list: Подходящие тайтлы в представлении каталога.
    """
    return await use_case.execute(build_autocomplete_anime_query(request, policy))


@anime_router.get(
    "/api/catalog", name="anime.filter_anime_catalog", response_model=AnimeCatalogPage
)
@rate_limit(
    scope="anime_catalog",
    limit=60,
    window_seconds=60,
    key_builder=lambda request: client_ip(request),
)
async def filter_anime_catalog(
    request: Request,
    use_case: FromDishka[FilterAnimeCatalogUseCase],
) -> AnimeCatalogPage:
    """Выдать каталог с фильтрами в стиле Anixart.

    Args:
        request: Текущий HTTP-запрос с параметрами фильтров и пагинации.
        use_case: Сценарий фильтрации каталога.

    Returns:
        AnimeCatalogPage: Страница каталога с фасетами жанров.
    """
    return await use_case.execute(build_filter_anime_catalog_query(request))


@anime_router.get(
    "/api/season/popular",
    name="anime.get_season_popular",
    response_model=list[AnimeCardResponse],
)
@rate_limit(
    scope="anime_season_popular",
    limit=60,
    window_seconds=60,
    key_builder=lambda request: client_ip(request),
)
async def get_season_popular(
    request: Request,
    use_case: FromDishka[GetSeasonPopularUseCase],
    policy: FromDishka[CatalogLimitsPolicy],
) -> list:
    """Выдать популярное аниме за сезон.

    Args:
        request: Текущий HTTP-запрос с параметрами сезона и года.
        use_case: Сценарий популярного за сезон.
        policy: Лимиты строк и выборки каталога.

    Returns:
        list: Популярные тайтлы сезона в представлении каталога.
    """
    return await use_case.execute(build_get_season_popular_query(request, policy))
