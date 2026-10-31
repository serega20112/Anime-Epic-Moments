"""Служебный JSON-маршрут конфигурации возможностей API.

Клиент узнаёт отсюда, какие возможности включены конфигом, чтобы не строить
интерфейс вслепую и не получать отказы там, где функция заведомо выключена.
"""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from backend.application.policies import ApiFeatureFlags
from backend.presentation.api.responses.api_config_responses import ApiConfigResponse
from backend.presentation.api.version import API_PREFIX, API_VERSION

api_config_router = APIRouter(prefix=API_PREFIX, route_class=DishkaRoute)


@api_config_router.get("/config", name="api.config", response_model=ApiConfigResponse)
async def api_config(flags: FromDishka[ApiFeatureFlags]) -> ApiConfigResponse:
    """Отдать клиенту включённые возможности JSON API.

    Args:
        flags: Фиче-флаги, собранные из конфигурации приложения.

    Returns:
        ApiConfigResponse: Версия API и состояние включённых возможностей.
    """
    return ApiConfigResponse(
        api_version=API_VERSION,
        adult_sources_enabled=flags.adult_sources_enabled,
        manual_source_creation_enabled=flags.manual_source_creation_enabled,
    )
