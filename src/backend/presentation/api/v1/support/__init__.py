"""Маршруты поддержки.

Функции живут в модуле ``tickets`` (он несёт префикс ``/support`` из-за пустого
корневого пути), а ``support_router``-агрегатор объявляется здесь.
"""

from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from backend.presentation.api.v1.support.tickets import tickets_router

support_router = APIRouter(route_class=DishkaRoute)

support_router.include_router(tickets_router)

__all__ = ["support_router"]
