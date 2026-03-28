from flask import Blueprint, request, jsonify, render_template
from src.backend.dependencies.container import container
from src.backend.infrastructure.security.flask_protection import rate_limit

anime_bp = Blueprint("anime", __name__, url_prefix="/anime")
QUERY_LIMIT_MAX = 50
TITLE_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 500
GENRE_HINT_MAX_LENGTH = 80


def _to_int(value: str | None) -> int | None:
    """Преобразует query-параметр в int или возвращает None."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _to_bool(value: str | None) -> bool:
    """Преобразует query-параметр в bool."""
    if not value:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _to_int_with_default(value: str | None, default: int) -> int:
    try:
        return int(value) if value not in (None, "") else int(default)
    except (TypeError, ValueError):
        return int(default)


def _validate_text(value: str | None, max_length: int) -> str:
    return str(value or "").strip()[: max(int(max_length), 1)]


@anime_bp.route("/search", methods=["GET"])
def search_anime_page():
    return render_template(
        "anime/search.html", initial_title=request.args.get("title", "")
    )


@anime_bp.route("/search/description", methods=["GET"])
def search_by_description_page():
    return render_template("anime/search_by_description.html")


@anime_bp.route("/api/search", methods=["GET"])
@rate_limit(
    container_getter=lambda: container,
    scope="anime_search",
    limit=60,
    window_seconds=60,
)
def search_anime():
    title = _validate_text(request.args.get("title", ""), TITLE_MAX_LENGTH)
    limit = min(max(_to_int_with_default(request.args.get("limit"), 10), 1), QUERY_LIMIT_MAX)
    if not title:
        return jsonify([])
    results = container.search_anime_use_case().execute(title=title, limit=limit)
    return jsonify([vars(anime) for anime in results])


@anime_bp.route("/api/search/description", methods=["GET"])
@rate_limit(
    container_getter=lambda: container,
    scope="anime_search_description",
    limit=30,
    window_seconds=60,
)
def search_anime_by_description():
    """Возвращает аниме, найденные по описанию и optional genre_hint."""
    desc = _validate_text(request.args.get("description", ""), DESCRIPTION_MAX_LENGTH)
    genre_hint = _validate_text(request.args.get("genre_hint"), GENRE_HINT_MAX_LENGTH) or None
    limit = min(max(_to_int_with_default(request.args.get("limit"), 10), 1), QUERY_LIMIT_MAX)
    sort_by = request.args.get("sort", "match")
    age_rating = request.args.get("age_rating", "all")
    adult_confirmed = _to_bool(request.args.get("adult_confirmed"))
    year_from = _to_int(request.args.get("year_from"))
    year_to = _to_int(request.args.get("year_to"))
    min_rating = _to_int(request.args.get("rating"))
    if not desc:
        return jsonify({"items": []})
    result = container.search_anime_by_description_use_case().execute(
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
    return jsonify(result.to_dict())


@anime_bp.route("/api/autocomplete", methods=["GET"])
@rate_limit(
    container_getter=lambda: container,
    scope="anime_autocomplete",
    limit=90,
    window_seconds=60,
)
def autocomplete_anime():
    query = _validate_text(request.args.get("query", ""), TITLE_MAX_LENGTH)
    limit = min(max(_to_int_with_default(request.args.get("limit"), 5), 1), 20)
    if not query:
        return jsonify([])
    suggestions = container.autocomplete_anime_use_case().execute(
        query=query, limit=limit
    )
    return jsonify([vars(anime) for anime in suggestions])


@anime_bp.route("/api/season/popular", methods=["GET"])
@rate_limit(
    container_getter=lambda: container,
    scope="anime_season_popular",
    limit=60,
    window_seconds=60,
)
def get_season_popular():
    year = _to_int(request.args.get("year"))
    season = str(request.args.get("season") or "").strip()
    limit = min(max(_to_int_with_default(request.args.get("limit"), 10), 1), QUERY_LIMIT_MAX)
    if year is None or not season:
        return jsonify({"error": "invalid_query"}), 400
    results = container.get_season_popular_use_case().execute(
        year=year, season=season, limit=limit
    )
    return jsonify([vars(anime) for anime in results])
