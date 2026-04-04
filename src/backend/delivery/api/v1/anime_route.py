from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.backend.delivery.api.helpers import get_container
from src.backend.infrastructure.security.flask_protection import client_ip, rate_limit
from src.backend.infrastructure.web.templating import render_template

anime_router = APIRouter(prefix="/anime")
anime_bp = anime_router
container = None
QUERY_LIMIT_MAX = 50
TITLE_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 500
GENRE_HINT_MAX_LENGTH = 80


def _to_int(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _to_bool(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _to_int_with_default(value: str | None, default: int) -> int:
    try:
        return int(value) if value not in (None, "") else int(default)
    except (TypeError, ValueError):
        return int(default)


def _validate_text(value: str | None, max_length: int) -> str:
    return str(value or "").strip()[: max(int(max_length), 1)]


@anime_router.get("/search", name="anime.search_anime_page")
async def search_anime_page(request: Request):
    return render_template(
        request,
        "anime/search.html",
        initial_title=request.query_params.get("title", ""),
    )


@anime_router.get("/search/description", name="anime.search_by_description_page")
async def search_by_description_page(request: Request):
    return render_template(request, "anime/search_by_description.html")


@anime_router.get("/api/search", name="anime.search_anime")
@rate_limit(
    scope="anime_search",
    limit=60,
    window_seconds=60,
    key_builder=lambda request: client_ip(request),
)
async def search_anime(request: Request):
    container = get_container(request)
    title = _validate_text(request.query_params.get("title", ""), TITLE_MAX_LENGTH)
    limit = min(
        max(_to_int_with_default(request.query_params.get("limit"), 10), 1),
        QUERY_LIMIT_MAX,
    )
    if not title:
        return []
    results = await container.search_anime_use_case().execute(title=title, limit=limit)
    return [vars(anime) for anime in results]


@anime_router.get("/api/search/description", name="anime.search_anime_by_description")
@rate_limit(
    scope="anime_search_description",
    limit=30,
    window_seconds=60,
    key_builder=lambda request: client_ip(request),
)
async def search_anime_by_description(request: Request):
    container = get_container(request)
    desc = _validate_text(
        request.query_params.get("description", ""),
        DESCRIPTION_MAX_LENGTH,
    )
    genre_hint = (
        _validate_text(request.query_params.get("genre_hint"), GENRE_HINT_MAX_LENGTH)
        or None
    )
    limit = min(
        max(_to_int_with_default(request.query_params.get("limit"), 10), 1),
        QUERY_LIMIT_MAX,
    )
    sort_by = request.query_params.get("sort", "match")
    age_rating = request.query_params.get("age_rating", "all")
    adult_confirmed = _to_bool(request.query_params.get("adult_confirmed"))
    year_from = _to_int(request.query_params.get("year_from"))
    year_to = _to_int(request.query_params.get("year_to"))
    min_rating = _to_int(request.query_params.get("rating"))
    if not desc:
        return {"items": []}
    result = await container.search_anime_by_description_use_case().execute(
        description=desc,
        genre_hint=genre_hint,
        year_from=year_from,
        year_to=year_to,
        min_rating=min_rating,
        age_rating=age_rating,
        adult_confirmed=adult_confirmed,
        sort_by=sort_by,
        limit=limit,
    )
    return result.to_dict()


@anime_router.get("/api/autocomplete", name="anime.autocomplete_anime")
@rate_limit(
    scope="anime_autocomplete",
    limit=90,
    window_seconds=60,
    key_builder=lambda request: client_ip(request),
)
async def autocomplete_anime(request: Request):
    container = get_container(request)
    query = _validate_text(request.query_params.get("query", ""), TITLE_MAX_LENGTH)
    limit = min(max(_to_int_with_default(request.query_params.get("limit"), 5), 1), 20)
    if not query:
        return []
    suggestions = await container.autocomplete_anime_use_case().execute(
        query=query,
        limit=limit,
    )
    return [vars(anime) for anime in suggestions]


@anime_router.get("/api/season/popular", name="anime.get_season_popular")
@rate_limit(
    scope="anime_season_popular",
    limit=60,
    window_seconds=60,
    key_builder=lambda request: client_ip(request),
)
async def get_season_popular(request: Request):
    container = get_container(request)
    year = _to_int(request.query_params.get("year"))
    season = str(request.query_params.get("season") or "").strip()
    limit = min(
        max(_to_int_with_default(request.query_params.get("limit"), 10), 1),
        QUERY_LIMIT_MAX,
    )
    if year is None or not season:
        return JSONResponse({"error": "invalid_query"}, status_code=400)
    results = await container.get_season_popular_use_case().execute(
        year=year,
        season=season,
        limit=limit,
    )
    return [vars(anime) for anime in results]
