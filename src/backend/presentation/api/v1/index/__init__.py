"""Маршрут главной страницы.

Функция отрисовки живёт в модуле ``home``, а ``index_router`` объявляется здесь.
"""

from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from backend.presentation.api.v1.index.home import home_router

index_router = APIRouter(route_class=DishkaRoute)

index_router.include_router(home_router)

__all__ = ["index_router"]
