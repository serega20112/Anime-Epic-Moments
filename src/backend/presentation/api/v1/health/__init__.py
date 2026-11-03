"""Маршруты проб живости и готовности.

Функции проб живут в модуле ``probes``, а ``health_router`` объявляется здесь.
"""

from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from backend.presentation.api.v1.health.probes import probes_router

health_router = APIRouter(route_class=DishkaRoute)

health_router.include_router(probes_router)

__all__ = ["health_router"]
