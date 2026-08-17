"""Thin HTTP route for the home page."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.use_cases.anime.get_home_page import GetHomePageUseCase
from backend.infrastructure.web import render_template

index_router = APIRouter(route_class=DishkaRoute)
index_bp = index_router


@index_router.get("/", name="index.index")
async def index(request: Request, use_case: FromDishka[GetHomePageUseCase]):
    """Render the home page with the current anime season context.

    Args:
        request: Incoming HTTP request.
        use_case: Home page use case.

    Returns:
        HTMLResponse: Rendered home page template.
    """
    current_season = await use_case.execute()
    return await render_template(
        request,
        "index.html",
        popular_anime=[],
        recommendations=[],
        home_year=current_season.year,
        home_season=current_season.season,
    )
