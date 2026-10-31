"""Маршруты страницы просмотра и короткого редиректа на неё."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from backend.application.dto import AnimeDiscussionQuery
from backend.application.use_cases import GetAnimeDiscussionUseCase
from backend.application.use_cases.watch.page.get_watch_page import GetWatchPageUseCase
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.requests.watch_mapper import map_watch_page_query
from backend.presentation.api.v1.watch_route.helpers import DISCUSSION_PREVIEW_LIMIT
from backend.presentation.web import render_template

page_router = APIRouter(route_class=DishkaRoute)


@page_router.get("/{anime_id}", name="watch.watch_page")
async def watch_page(
    request: Request,
    anime_id: int,
    watch_use_case: FromDishka[GetWatchPageUseCase],
    discussion_use_case: FromDishka[GetAnimeDiscussionUseCase],
):
    """Отдать страницу просмотра аниме вместе с обсуждением серии.

    Args:
        request: Текущий HTTP-запрос.
        anime_id: Идентификатор аниме из пути.
        watch_use_case: Сценарий сборки страницы просмотра.
        discussion_use_case: Сценарий чтения обсуждения аниме.

    Returns:
        Response: Отрисованная страница просмотра.
    """
    user = await get_current_user(request)
    user_id = user.id if user else None
    query = map_watch_page_query(request, anime_id=anime_id, user_id=user_id)
    data = await watch_use_case.execute(query)
    discussion = await discussion_use_case.execute(
        AnimeDiscussionQuery(
            anime_id=anime_id,
            sort_by=query.discussion_sort,
            viewer_user_id=user_id,
            limit=DISCUSSION_PREVIEW_LIMIT,
        )
    )
    return await render_template(
        request, "anime/watch.html", watch=data, discussion=discussion.data
    )


@page_router.get("/open/{anime_id}", name="watch.redirect_to_watch")
async def redirect_to_watch(request: Request, anime_id: int):
    """Перенаправить на страницу просмотра аниме.

    Args:
        request: Текущий HTTP-запрос.
        anime_id: Идентификатор аниме из пути.

    Returns:
        RedirectResponse: Редирект 303 на страницу просмотра выбранной серии.
    """
    query = map_watch_page_query(request, anime_id=anime_id, user_id=None)
    url = request.app.url_path_for("watch.watch_page", anime_id=str(anime_id))
    return RedirectResponse(
        url=f"{url}?episode={query.episode}",
        status_code=HTTPStatus.SEE_OTHER,
    )
