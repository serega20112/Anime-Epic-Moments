"""Маршруты рекомендаций аниме.

Действия живут в модуле ``actions``, а ``recommendation_router`` с префиксом
JSON-API собирается здесь.
"""

from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from backend.presentation.api.v1.recommendations.actions import recommendation_actions_router
from backend.presentation.api.version import API_PREFIX

recommendation_router = APIRouter(prefix=f"{API_PREFIX}/recommendations", route_class=DishkaRoute)

recommendation_router.include_router(recommendation_actions_router)

__all__ = ["recommendation_router"]
