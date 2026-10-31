"""Тонкие HTTP-маршруты моментов просмотра и их черновиков."""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.dto import (
    DeleteViewingMomentCommand,
    GetUserViewingMomentsQuery,
    PublishViewingMomentCommand,
    SaveViewingMomentCommand,
)
from backend.application.use_cases import (
    DeleteViewingMomentUseCase,
    GetUserViewingMomentsUseCase,
    PublishViewingMomentUseCase,
    SaveViewingMomentUseCase,
)
from backend.presentation.api.errors import ErrorResponse, error_from_result, unauthorized_error
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.requests.moment_requests import (
    PublishViewingMomentRequest,
    SaveViewingMomentRequest,
)
from backend.presentation.api.responses.moment_responses import (
    MomentDeletedResponse,
    PublishMomentResponse,
    ViewingMomentResponse,
)

watch_moment_router = APIRouter(prefix="/watch", route_class=DishkaRoute)
moment_router = APIRouter(prefix="/moments", route_class=DishkaRoute)

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


@moment_router.get(
    "",
    name="moment.get_user_moments",
    response_model=list[ViewingMomentResponse],
    responses={"401": {"model": ErrorResponse}},
)
async def get_user_moments(
    request: Request,
    use_case: FromDishka[GetUserViewingMomentsUseCase],
):
    """Отдать черновики моментов текущего пользователя.

    Args:
        request: Текущий HTTP-запрос.
        use_case: Сценарий списка черновиков.

    Returns:
        list[ViewingMomentResponse]: Черновики пользователя сессии.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    result = await use_case.execute(GetUserViewingMomentsQuery(user_id=user.id))
    return [
        ViewingMomentResponse.model_validate(item, from_attributes=True) for item in result.data
    ]


@moment_router.post(
    "/{moment_id}/publish",
    name="moment.publish_moment",
    response_model=PublishMomentResponse,
    responses=_ERROR_RESPONSES,
)
async def publish_moment(
    request: Request,
    moment_id: int,
    body: PublishViewingMomentRequest,
    use_case: FromDishka[PublishViewingMomentUseCase],
):
    """Опубликовать черновик момента как хайлайт.

    Args:
        request: Текущий HTTP-запрос.
        moment_id: Идентификатор черновика из пути.
        body: Тело запроса с параметрами хайлайта.
        use_case: Сценарий публикации момента.

    Returns:
        PublishMomentResponse: Идентификатор созданного хайлайта либо тело ошибки.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    result = await use_case.execute(
        PublishViewingMomentCommand(
            user_id=user.id,
            moment_id=moment_id,
            is_spoiler=body.is_spoiler,
            title=body.title,
            category=body.category,
            emotion=body.emotion,
            description=body.description,
        )
    )
    if not result.ok:
        return error_from_result(result)
    return PublishMomentResponse(highlight_id=result.data.id)


@moment_router.delete(
    "/{moment_id}",
    name="moment.delete_moment",
    response_model=MomentDeletedResponse,
    responses=_ERROR_RESPONSES,
)
async def delete_moment(
    request: Request,
    moment_id: int,
    use_case: FromDishka[DeleteViewingMomentUseCase],
):
    """Удалить черновик момента просмотра.

    Args:
        request: Текущий HTTP-запрос.
        moment_id: Идентификатор черновика из пути.
        use_case: Сценарий удаления черновика.

    Returns:
        MomentDeletedResponse: Подтверждение удаления либо тело ошибки.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    result = await use_case.execute(
        DeleteViewingMomentCommand(moment_id=moment_id, user_id=user.id)
    )
    if not result.ok:
        return error_from_result(result)
    return MomentDeletedResponse.model_validate(result.data)
