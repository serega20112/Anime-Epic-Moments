from flask import Blueprint, request, jsonify, render_template
from src.backend.dependencies.container import container

anime_bp = Blueprint("anime", __name__, url_prefix="/anime")


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


@anime_bp.route("/search", methods=["GET"])
def search_anime_page():
    return render_template("anime/search.html", initial_title=request.args.get("title", ""))


@anime_bp.route("/search/description", methods=["GET"])
def search_by_description_page():
    return render_template("anime/search_by_description.html")


@anime_bp.route("/api/search", methods=["GET"])
def search_anime():
    title = request.args.get("title", "")
    limit = int(request.args.get("limit", 10))
    results = container.search_anime_use_case().execute(title=title, limit=limit)
    return jsonify([vars(anime) for anime in results])


@anime_bp.route("/api/search/description", methods=["GET"])
def search_anime_by_description():
    """Возвращает аниме, найденные по описанию и optional genre_hint."""
    desc = request.args.get("description", "")
    genre_hint = request.args.get("genre_hint")
    limit = int(request.args.get("limit", 10))
    sort_by = request.args.get("sort", "match")
    age_rating = request.args.get("age_rating", "all")
    adult_confirmed = _to_bool(request.args.get("adult_confirmed"))
    year_from = _to_int(request.args.get("year_from"))
    year_to = _to_int(request.args.get("year_to"))
    min_rating = _to_int(request.args.get("rating"))
    result = container.search_anime_by_description_use_case().execute(
        description=desc,
        genre_hint=genre_hint,
        year_from=year_from,
        year_to=year_to,
        min_rating=min_rating,
        age_rating=age_rating,
        adult_confirmed=adult_confirmed,
        sort_by=sort_by,
        limit=limit
    )
    return jsonify(result.to_dict())


@anime_bp.route("/api/autocomplete", methods=["GET"])
def autocomplete_anime():
    query = request.args.get("query", "")
    limit = int(request.args.get("limit", 5))
    suggestions = container.autocomplete_anime_use_case().execute(query=query, limit=limit)
    return jsonify([vars(anime) for anime in suggestions])


@anime_bp.route("/api/season/popular", methods=["GET"])
def get_season_popular():
    year = int(request.args.get("year"))
    season = request.args.get("season")
    limit = int(request.args.get("limit", 10))
    results = container.get_season_popular_use_case().execute(year=year, season=season, limit=limit)
    return jsonify([vars(anime) for anime in results])
