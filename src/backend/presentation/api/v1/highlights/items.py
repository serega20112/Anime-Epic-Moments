"""Маршруты создания, правки и удаления хайлайтов."""

from __future__ import annotations

import logging
from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.interface.services import RateLimiterInterface
from backend.application.use_cases import DeleteHighlightUseCase, EditHighlightUseCase
from backend.application.use_cases.highlight.crud.create_highlight import CreateHighlightUseCase
from backend.presentation.api.errors import ErrorResponse, error_from_result, unauthorized_error
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.rate_limit import client_ip, rate_limit
from backend.presentation.api.requests.highlight_mapper import (
    map_create_highlight_command,
    map_delete_highlight_command,
    map_edit_highlight_command,
)
from backend.presentation.api.requests.highlight_requests import (
    CreateHighlightRequest,
    EditHighlightRequest,
)
from backend.presentation.api.responses.highlight_responses import HighlightIdResponse

logger = logging.getLogger("anime_epic_moments")

highlight_items_router = APIRouter(route_class=DishkaRoute)

HIGHLIGHT_CREATE_SCOPE = "highlight_create"
HIGHLIGHT_CREATE_WINDOW_SECONDS = 60

_ERROR_RESPONSES = {
    "400": {"model": ErrorResponse},
    "401": {"model": ErrorResponse},
    "403": {"model": ErrorResponse},
    "404": {"model": ErrorResponse},
    "429": {"model": ErrorResponse},
}


async def _create_highlight_subject(request: Request) -> str:
    """Собрать составной ключ ограничения частоты для создания хайлайта.

    Args:
        request: Текущий HTTP-запрос.

    Returns:
        str: Ключ из адреса клиента и идентификатора автора или слова ``guest``.
    """
    ip = await client_ip(request)
    user_id = getattr(await get_current_user(request), "id", "guest")
    return f"{ip}::{user_id}"


async def _highlights_this_hour(request: Request, limiter: RateLimiterInterface) -> int:
    """Прочитать счётчик добавлений хайлайтов за текущее окно.

    Захват широкий намеренно: значение используется только как подсказка для
    гостевого лимита в политике, и сбой Redis не должен мешать создавать
    хайлайт. Отказ пишется в лог через ``logger.exception`` с путём запроса.

    Args:
        request: Текущий HTTP-запрос.
        limiter: Порт ограничителя частоты обращений.

    Returns:
        int: Число учтённых добавлений; 0, если лимитер недоступен.
    """
    try:
        return await limiter.current(
            scope=HIGHLIGHT_CREATE_SCOPE,
            subject=await _create_highlight_subject(request),
        )
    except Exception:
        logger.exception("highlight_quota_lookup_failed path=%s", request.url.path)
        return 0


@highlight_items_router.post(
    "/",
    name="highlight.create_highlight",
    status_code=HTTPStatus.CREATED,
    response_model=HighlightIdResponse,
    responses=_ERROR_RESPONSES,
)
@rate_limit(
    scope="highlight_create",
    limit=20,
    window_seconds=60,
    key_builder=_create_highlight_subject,
)
async def create_highlight(
    request: Request,
    body: CreateHighlightRequest,
    use_case: FromDishka[CreateHighlightUseCase],
    limiter: FromDishka[RateLimiterInterface],
):
    """Создать хайлайт по JSON-данным.

    Args:
        request: Текущий HTTP-запрос.
        body: Проверенное тело хайлайта.
        use_case: Сценарий создания хайлайта.
        limiter: Порт ограничителя для гостевой квоты.

    Returns:
        HighlightIdResponse: Идентификатор созданного хайлайта либо тело ошибки.
    """
    user = await get_current_user(request)
    result = await use_case.execute(
        map_create_highlight_command(
            body,
            user_id=user.id if user else None,
            highlights_this_hour=await _highlights_this_hour(request, limiter),
        )
    )
    if not result.ok:
        return error_from_result(result)
    return HighlightIdResponse(highlight_id=getattr(result.data, "id", None))


@highlight_items_router.put(
    "/{highlight_id}",
    name="highlight.edit_highlight",
    response_model=HighlightIdResponse,
    responses=_ERROR_RESPONSES,
)
async def edit_highlight(
    request: Request,
    highlight_id: int,
    body: EditHighlightRequest,
    use_case: FromDishka[EditHighlightUseCase],
):
    """Изменить существующий хайлайт.

    Args:
        request: Текущий HTTP-запрос.
        highlight_id: Идентификатор хайлайта из пути.
        body: Проверенное тело правки.
        use_case: Сценарий правки хайлайта.

    Returns:
        HighlightIdResponse: Идентификатор обновлённого хайлайта либо тело ошибки.
    """
    user = await get_current_user(request)
    if user is None:
        return unauthorized_error()
    result = await use_case.execute(
        map_edit_highlight_command(body, highlight_id=highlight_id, user_id=user.id)
    )
    if not result.ok:
        return error_from_result(result)
    return HighlightIdResponse(highlight_id=getattr(result.data, "id", highlight_id))


@highlight_items_router.delete(
    "/{highlight_id}",
    name="highlight.delete_highlight",
    status_code=HTTPStatus.NO_CONTENT,
    responses=_ERROR_RESPONSES,
)
async def delete_highlight(
    request: Request,
    highlight_id: int,
    use_case: FromDishka[DeleteHighlightUseCase],
):
    """Удалить хайлайт.

    Args:
        request: Текущий HTTP-запрос.
        highlight_id: Идентификатор хайлайта из пути.
        use_case: Сценарий удаления хайлайта.

    Returns:
        Response: Пустой ответ 204 либо тело ошибки.
    """
    user = await get_current_user(request)
    if user is None:
        return unauthorized_error()
    result = await use_case.execute(
        map_delete_highlight_command(highlight_id=highlight_id, user_id=user.id)
    )
    if not result.ok:
        return error_from_result(result)
