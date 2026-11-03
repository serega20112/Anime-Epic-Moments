"""Проверки живости и готовности процесса для оркестратора."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.application.interface.services import HealthCheckPort
from backend.presentation.api.responses.health_responses import LivenessResponse, ReadinessResponse

probes_router = APIRouter(route_class=DishkaRoute)

READY_RESPONSES = {"503": {"model": ReadinessResponse}}


@probes_router.get("/health", response_model=LivenessResponse)
async def health() -> LivenessResponse:
    """Сообщить, что процесс жив, не трогая зависимости.

    Returns:
        LivenessResponse: Метка живости процесса.
    """
    return LivenessResponse()


@probes_router.get("/ready", response_model=ReadinessResponse, responses=READY_RESPONSES)
async def ready(health_check: FromDishka[HealthCheckPort]) -> JSONResponse:
    """Сообщить готовность базы и дополнительных зависимостей.

    Ответ отдаётся JSONResponse вручную, потому что код статуса зависит от
    результата проверки: 200 при готовности и 503 при отказе зависимости.

    Args:
        health_check: Порт проверки готовности; как именно опрашиваются
            зависимости — дело инфраструктуры.

    Returns:
        JSONResponse: 200 с отметками по зависимостям либо 503 при отказе.
    """
    status = await health_check.check()
    status_code = HTTPStatus.OK if status.ready else HTTPStatus.SERVICE_UNAVAILABLE
    return JSONResponse(status.payload, status_code=status_code)
