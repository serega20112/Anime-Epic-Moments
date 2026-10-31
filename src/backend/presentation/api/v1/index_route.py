"""Маршрут главной страницы."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.dto.anime import HomePageQuery
from backend.application.use_cases.anime.get_home_page import GetHomePageUseCase
from backend.presentation.web import render_template

index_router = APIRouter(route_class=DishkaRoute)


@index_router.get("/", name="index.index")
async def index(request: Request, use_case: FromDishka[GetHomePageUseCase]):
    """Отрисовать главную страницу с сезоном текущего года.

    Args:
        request: Текущий HTTP-запрос.
        use_case: Сценарий получения данных главной страницы.

    Returns:
        HTMLResponse: Готовая страница с популярным и рекомендациями.
    """
    current_season = await use_case.execute(HomePageQuery())
    return await render_template(
        request,
        "index.html",
        popular_anime=[],
        recommendations=[],
        home_year=current_season.year,
        home_season=current_season.season,
    )
