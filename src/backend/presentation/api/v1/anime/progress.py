"""JSON-маршрут сохранения позиции просмотра для мобильного клиента."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.use_cases.watch.session.save_viewing_session import (
    SaveViewingSessionUseCase,
)
from backend.domain.policies.watch_policy import is_episode_watched
from backend.presentation.api.errors import error_from_result, unauthorized_error
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.requests.watch_mapper import map_save_progress_command
from backend.presentation.api.requests.watch_requests import SaveProgressRequest
from backend.presentation.api.responses.watch_responses import ProgressSavedResponse
from backend.presentation.api.v1.watch_route.helpers import ERROR_RESPONSES

progress_router = APIRouter(route_class=DishkaRoute)


@progress_router.post(
    "/{anime_id}/progress",
    name="api_anime.save_progress",
    response_model=ProgressSavedResponse,
    responses=ERROR_RESPONSES,
)
async def save_progress(
    request: Request,
    anime_id: int,
    body: SaveProgressRequest,
    use_case: FromDishka[SaveViewingSessionUseCase],
):
    """Сохранить позицию воспроизведения и вернуть признак «просмотрено».

    Args:
        request: Текущий HTTP-запрос с заголовком Authorization.
        anime_id: Идентификатор аниме из пути.
        body: Проверенное тело позиции мобильного плеера.
        use_case: Сценарий сохранения сессии просмотра.

    Returns:
        ProgressSavedResponse | Response: Итог сохранения либо тело отказа.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    result = await use_case.execute(
        map_save_progress_command(body, user_id=user.id, anime_id=anime_id)
    )
    if not result.ok:
        return error_from_result(result)
    return ProgressSavedResponse(
        saved=True,
        watched=is_episode_watched(body.position_seconds, body.duration_seconds),
    )
