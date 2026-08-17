"""Liveness and readiness endpoints for orchestration probes."""

from __future__ import annotations

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.files.database import get_session_factory

health_router = APIRouter(route_class=DishkaRoute)


@health_router.get("/health")
async def health() -> dict[str, str]:
    """Report process liveness without touching dependencies.

    Returns:
        dict[str, str]: Liveness payload.
    """
    return {"status": "ok"}


@health_router.get("/ready")
async def ready(store: FromDishka[KeyValueStore]) -> JSONResponse:
    """Report readiness of the database and optional Redis.

    Args:
        store: Application-wide key-value store.

    Returns:
        JSONResponse: 200 with per-dependency checks, 503 when any fails.
    """
    checks: dict[str, str] = {}
    is_ready = True

    try:
        session_factory = await get_session_factory()
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        is_ready = False
        checks["database"] = "unreachable"

    if store.uses_redis:
        try:
            if await store.ping():
                checks["redis"] = "ok"
            else:
                is_ready = False
                checks["redis"] = "unreachable"
        except Exception:
            is_ready = False
            checks["redis"] = "unreachable"
    else:
        checks["redis"] = "disabled"

    status_code = HTTPStatus.OK if is_ready else HTTPStatus.SERVICE_UNAVAILABLE
    return JSONResponse(
        {"status": "ready" if is_ready else "unavailable", "checks": checks},
        status_code=status_code,
    )
