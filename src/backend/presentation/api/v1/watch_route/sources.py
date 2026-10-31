"""Маршруты источников просмотра: ручная добавка и поиск у провайдера."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request

from backend.application.policies import ApiFeatureFlags
from backend.application.use_cases import AddWatchSourceUseCase, SyncWatchSourcesUseCase
from backend.presentation.api.errors import (
    ErrorResponse,
    error_from_result,
    error_response,
    unauthorized_error,
)
from backend.presentation.api.helpers import get_current_user
from backend.presentation.api.rate_limit import rate_limit
from backend.presentation.api.requests.watch_mapper import (
    map_add_watch_source_command,
    map_sync_sources_query,
)
from backend.presentation.api.requests.watch_requests import (
    AddWatchSourceRequest,
    DiscoverSourcesRequest,
)
from backend.presentation.api.responses.watch_responses import (
    DiscoverSourcesResponse,
    WatchSourceResponse,
)
from backend.presentation.api.v1.watch_route.helpers import (
    ERROR_RESPONSES,
    MANUAL_SOURCE_DISABLED_CODE,
    MANUAL_SOURCE_DISABLED_MESSAGE,
    discover_sources_subject,
)

sources_router = APIRouter(route_class=DishkaRoute)


@sources_router.post(
    "/{anime_id}/sources",
    name="watch.add_source",
    status_code=HTTPStatus.CREATED,
    response_model=WatchSourceResponse,
    responses=ERROR_RESPONSES,
)
async def add_source(
    request: Request,
    anime_id: int,
    body: AddWatchSourceRequest,
    use_case: FromDishka[AddWatchSourceUseCase],
    flags: FromDishka[ApiFeatureFlags],
):
    """Добавить источник просмотра вручную.

    Возможность включается конфигом: по умолчанию ручные источники запрещены,
    потому что поток с произвольного адреса проксируется через наш сервер.

    Args:
        request: Текущий HTTP-запрос.
        anime_id: Идентификатор аниме из пути.
        body: Проверенное тело источника.
        use_case: Сценарий создания озвучки и источника.
        flags: Фиче-флаги, разрешающие ручное добавление.

    Returns:
        WatchSourceResponse | Response: Созданный источник либо тело отказа.
    """
    user = await get_current_user(request)
    if not user:
        return unauthorized_error()
    if not flags.manual_source_creation_enabled:
        return error_response(
            MANUAL_SOURCE_DISABLED_CODE,
            MANUAL_SOURCE_DISABLED_MESSAGE,
            HTTPStatus.FORBIDDEN,
        )
    source = await use_case.execute(map_add_watch_source_command(body, anime_id=anime_id))
    return WatchSourceResponse(source_id=source.id, translation_id=source.translation_id)


@sources_router.post(
    "/{anime_id}/sources/discover",
    name="watch.discover_sources",
    response_model=DiscoverSourcesResponse,
    responses={
        "400": {"model": ErrorResponse},
        "404": {"model": ErrorResponse},
        "429": {"model": ErrorResponse},
        "504": {"model": ErrorResponse},
    },
)
@rate_limit(
    scope="watch_discover_sources",
    limit=15,
    window_seconds=60,
    key_builder=discover_sources_subject,
)
async def discover_sources(
    request: Request,
    anime_id: int,
    body: DiscoverSourcesRequest,
    use_case: FromDishka[SyncWatchSourcesUseCase],
):
    """Найти источники просмотра у внешнего провайдера.

    Args:
        request: Текущий HTTP-запрос.
        anime_id: Идентификатор аниме из пути.
        body: Проверенное тело с номером серии.
        use_case: Сценарий синхронизации источников.

    Returns:
        DiscoverSourcesResponse: Сводка по найденным источникам либо тело ошибки.
    """
    result = await use_case.execute(map_sync_sources_query(body, anime_id=anime_id))
    if not result.ok:
        return error_from_result(result)
    return DiscoverSourcesResponse.model_validate(result.data)
