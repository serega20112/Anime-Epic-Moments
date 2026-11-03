"""Маршруты избранного.

Изменение и чтение разнесены по модулям ``operations`` и ``queries``, а
``favorite_router`` с префиксом ``/favorites`` собирается здесь.
"""

from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from backend.presentation.api.v1.favorites.operations import favorite_ops_router
from backend.presentation.api.v1.favorites.queries import favorite_queries_router

favorite_router = APIRouter(prefix="/favorites", route_class=DishkaRoute)

favorite_router.include_router(favorite_ops_router)
favorite_router.include_router(favorite_queries_router)

__all__ = ["favorite_router"]
