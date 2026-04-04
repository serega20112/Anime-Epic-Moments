from datetime import datetime

from fastapi import APIRouter, Request

from src.backend.infrastructure.web.templating import render_template

index_router = APIRouter()
index_bp = index_router
container = None


@index_router.get("/", name="index.index")
async def index(request: Request):
    home_year, home_season = _resolve_current_anime_season()
    return render_template(
        request,
        "index.html",
        popular_anime=[],
        recommendations=[],
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
