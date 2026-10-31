"""Маршруты дневника просмотра: статус, позиция серии и завершение серии."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.use_cases import (
    CompleteEpisodeUseCase,
    UpsertUserAnimeStatusUseCase,
)
from backend.application.use_cases.watch.session.save_viewing_session import (
    SaveViewingSessionUseCase,
)
from backend.presentation.api.errors import error_from_result, unauthorized_error
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.requests.watch_mapper import (
    map_complete_episode_command,
    map_save_session_command,
    map_upsert_status_command,
)
from backend.presentation.api.requests.watch_requests import (
    CompleteEpisodeRequest,
    SaveViewingSessionRequest,
    UpdateWatchStatusRequest,
)
from backend.presentation.api.responses.watch_responses import (
    EpisodeCompletionResponse,
    WatchSessionResponse,
    WatchStatusResponse,
)
from backend.presentation.api.v1.watch_route.helpers import ERROR_RESPONSES

sessions_router = APIRouter(route_class=DishkaRoute)


@sessions_router.post(
    "/{anime_id}/status",
    name="watch.update_status",
    response_model=WatchStatusResponse,
    responses=ERROR_RESPONSES,
)
async def update_status(
    request: Request,
    anime_id: int,
    body: UpdateWatchStatusRequest,
    use_case: FromDishka[UpsertUserAnimeStatusUseCase],
):
    """Обновить статус просмотра аниме у пользователя.

    Args:
        request: Текущий HTTP-запрос.
        anime_id: Идентификатор аниме из пути.
        body: Проверенное тело статуса.
        use_case: Сценарий upsert статуса просмотра.

    Returns:
        WatchStatusResponse: Записанный статус либо тело ошибки.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    result = await use_case.execute(
        map_upsert_status_command(body, user_id=user.id, anime_id=anime_id)
    )
    if not result.ok:
        return error_from_result(result)
    return WatchStatusResponse(status=result.data.status)


@sessions_router.post(
    "/{anime_id}/session",
    name="watch.save_session",
    response_model=WatchSessionResponse,
    responses=ERROR_RESPONSES,
)
async def save_session(
    request: Request,
    anime_id: int,
    body: SaveViewingSessionRequest,
    use_case: FromDishka[SaveViewingSessionUseCase],
):
    """Сохранить позицию просмотра пользователя.

    Args:
        request: Текущий HTTP-запрос.
        anime_id: Идентификатор аниме из пути.
        body: Проверенное тело состояния плеера.
        use_case: Сценарий сохранения сессии просмотра.

    Returns:
        WatchSessionResponse: Идентификатор сессии либо тело ошибки.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    result = await use_case.execute(
        map_save_session_command(body, user_id=user.id, anime_id=anime_id)
    )
    if not result.ok:
        return error_from_result(result)
    return WatchSessionResponse(session_id=result.data.id)


@sessions_router.post(
    "/{anime_id}/episode/complete",
    name="watch.complete_episode",
    response_model=EpisodeCompletionResponse,
    responses=ERROR_RESPONSES,
)
async def complete_episode(
    request: Request,
    anime_id: int,
    body: CompleteEpisodeRequest,
    use_case: FromDishka[CompleteEpisodeUseCase],
):
    """Отметить, что пользователь досмотрел серию.

    Args:
        request: Текущий HTTP-запрос.
        anime_id: Идентификатор аниме из пути.
        body: Проверенное тело с номером серии.
        use_case: Сценарий завершения эпизода.

    Returns:
        EpisodeCompletionResponse: Обновлённый прогресс либо тело ошибки.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    result = await use_case.execute(
        map_complete_episode_command(body, user_id=user.id, anime_id=anime_id)
    )
    if not result.ok:
        return error_from_result(result)
    return EpisodeCompletionResponse.model_validate(result.data, from_attributes=True)
