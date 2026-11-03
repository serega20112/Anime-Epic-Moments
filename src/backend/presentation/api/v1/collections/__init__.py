"""JSON-маршруты коллекций мобильного клиента.

Функции разнесены по модулям сценариев (``items``, ``user_collections``), единый
``api_collections_router`` собирается здесь. Префиксы несут дочерние роутеры, а
не родитель: маршруты элемента живут под ``/api/v1/collections``, а список и
создание — под ``/api/v1/users``; у двух разных префиксов нет общего корня,
поэтому родитель остаётся агрегатором без префикса.
"""

from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from backend.presentation.api.v1.collections.items import items_router
from backend.presentation.api.v1.collections.user_collections import (
    user_collections_router,
)
from backend.presentation.api.v1.collections.web import collection_router

api_collections_router = APIRouter(route_class=DishkaRoute)

api_collections_router.include_router(user_collections_router)
api_collections_router.include_router(items_router)

__all__ = ["api_collections_router", "collection_router"]
