from datetime import datetime

from flask import Blueprint, render_template, g

index_bp = Blueprint("index", __name__, url_prefix="/")


@index_bp.route("/", methods=["GET"])
def index():
    """Главная страница"""
    user = g.user
    home_year, home_season = _resolve_current_anime_season()

    return render_template(
        "index.html",
        popular_anime=[],
        recommendations=[],
        current_user=user,
        home_year=home_year,
        home_season=home_season,
    )


def _resolve_current_anime_season(now: datetime | None = None) -> tuple[int, str]:
    current = now or datetime.utcnow()
    month = int(current.month)
    if month in {12, 1, 2}:
        return int(current.year), "winter"
    if month in {3, 4, 5}:
        return int(current.year), "spring"
    if month in {6, 7, 8}:
        return int(current.year), "summer"
    return int(current.year), "fall"
