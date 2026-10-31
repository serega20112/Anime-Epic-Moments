"""Маршрут создания хайлайта из плеера."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.use_cases.watch.highlight.create_watch_highlight import (
    CreateWatchHighlightUseCase,
)
from backend.presentation.api.errors import error_from_result, unauthorized_error
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.rate_limit import rate_limit
from backend.presentation.api.requests.watch_mapper import (
    map_create_watch_highlight_command,
)
from backend.presentation.api.requests.watch_requests import CreateWatchHighlightRequest
from backend.presentation.api.responses.watch_responses import WatchHighlightResponse
from backend.presentation.api.v1.watch_route.helpers import (
    ERROR_RESPONSES,
    create_watch_highlight_subject,
)

highlights_router = APIRouter(route_class=DishkaRoute)


@highlights_router.post(
    "/{anime_id}/highlights",
    name="watch.create_highlight",
    status_code=HTTPStatus.CREATED,
    response_model=WatchHighlightResponse,
    responses=ERROR_RESPONSES,
)
@rate_limit(
    scope="watch_create_highlight",
    limit=20,
    window_seconds=60,
    key_builder=create_watch_highlight_subject,
)
async def create_highlight(
    request: Request,
    anime_id: int,
    body: CreateWatchHighlightRequest,
    use_case: FromDishka[CreateWatchHighlightUseCase],
):
    """Создать хайлайт из плеера.

    Args:
        request: Текущий HTTP-запрос.
        anime_id: Идентификатор аниме из пути.
        body: Проверенное тело хайлайта.
        use_case: Сценарий создания хайлайта из плеера.

    Returns:
        WatchHighlightResponse: Идентификатор хайлайта либо тело ошибки.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    result = await use_case.execute(
        map_create_watch_highlight_command(body, user_id=user.id, anime_id=anime_id)
    )
    if not result.ok:
        return error_from_result(result)
    return WatchHighlightResponse(highlight_id=result.data.id)
