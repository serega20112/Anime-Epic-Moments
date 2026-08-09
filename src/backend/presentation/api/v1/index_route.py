"""Thin HTTP route for the home page."""

from __future__ import annotations

from fastapi import APIRouter, Request

from backend.infrastructure.web import render_template
from backend.presentation.api.helpers import get_container

index_router = APIRouter()
index_bp = index_router


@index_router.get("/", name="index.index")
async def index(request: Request):
    """Render the home page with the current anime season context.

    Args:
        request: Incoming HTTP request.

    Returns:
        HTMLResponse: Rendered home page template.
    """
    container = get_container(request)
    current_season = container.get_home_page_use_case().execute()
    return render_template(
        request,
        "index.html",
        popular_anime=[],
        recommendations=[],
        home_year=current_season.year,
        home_season=current_season.season,
    )
