"""HTTP-маршрут сохранения черновика момента из плеера."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.dto import SaveViewingMomentCommand
from backend.application.use_cases import SaveViewingMomentUseCase
from backend.presentation.api.errors import ErrorResponse, error_from_result, unauthorized_error
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.requests.moment_requests import SaveViewingMomentRequest
from backend.presentation.api.responses.moment_responses import ViewingMomentResponse

watch_moment_router = APIRouter(prefix="/watch", route_class=DishkaRoute)

_ERROR_RESPONSES = {
    "400": {"model": ErrorResponse},
    "401": {"model": ErrorResponse},
    "404": {"model": ErrorResponse},
}


@watch_moment_router.post(
    "/{anime_id}/moments",
    name="watch.save_moment",
    response_model=ViewingMomentResponse,
    responses=_ERROR_RESPONSES,
)
async def save_moment(
    request: Request,
    anime_id: int,
    body: SaveViewingMomentRequest,
    use_case: FromDishka[SaveViewingMomentUseCase],
):
    """Создать или обновить черновик момента из плеера.

    Args:
        request: Текущий HTTP-запрос.
        anime_id: Идентификатор аниме из пути.
        body: Тело запроса с данными момента.
        use_case: Сценарий сохранения черновика.

    Returns:
        ViewingMomentResponse: Сохранённый черновик либо тело ошибки.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    result = await use_case.execute(
        SaveViewingMomentCommand(
            user_id=user.id,
            anime_id=anime_id,
            episode=body.episode,
            timestamp=body.timestamp,
            watch_source_id=body.watch_source_id,
            caption=body.caption,
            sticker=body.sticker,
            screenshot_url=body.screenshot_url,
            moment_id=body.moment_id,
        )
    )
    if not result.ok:
        return error_from_result(result)
    return ViewingMomentResponse.model_validate(result.data, from_attributes=True)
