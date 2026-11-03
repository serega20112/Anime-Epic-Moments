"""Служебный JSON-маршрут конфигурации возможностей API.

Клиент узнаёт отсюда, какие возможности включены конфигом, чтобы не строить
интерфейс вслепую и не получать отказы там, где функция заведомо выключена.
Единственный эндпоинт объявлен прямо в фасадном модуле пакета.
"""

from __future__ import annotations

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from backend.application.policies import ApiFeatureFlags, AppReleaseInfo
from backend.presentation.api.responses.api_config_responses import ApiConfigResponse
from backend.presentation.api.version import API_PREFIX, API_VERSION

api_config_router = APIRouter(prefix=API_PREFIX, route_class=DishkaRoute)


@api_config_router.get("/config", name="api.config", response_model=ApiConfigResponse)
async def api_config(
    flags: FromDishka[ApiFeatureFlags],
    release: FromDishka[AppReleaseInfo],
) -> ApiConfigResponse:
    """Отдать клиенту включённые возможности JSON API и сведения о релизе.

    Args:
        flags: Фиче-флаги, собранные из конфигурации приложения.
        release: Сведения о релизе мобильного приложения из конфигурации.

    Returns:
        ApiConfigResponse: Версия API, возможности и параметры релиза.
    """
    return ApiConfigResponse(
        api_version=API_VERSION,
        adult_sources_enabled=flags.adult_sources_enabled,
        manual_source_creation_enabled=flags.manual_source_creation_enabled,
        latest_app_version=release.latest_app_version,
        min_app_version=release.min_app_version,
        apk_url=release.apk_url,
        apk_sha256=release.apk_sha256,
        changelog_url=release.changelog_url,
        maintenance_mode=release.maintenance_mode,
    )
