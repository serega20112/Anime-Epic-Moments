"""Маршруты оценок аниме.

Функция формы живёт в модуле ``rating``, а ``rating_router`` с префиксом
``/ratings`` объявляется здесь.
"""

from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from backend.presentation.api.v1.ratings.rating import rating_form_router

rating_router = APIRouter(prefix="/ratings", route_class=DishkaRoute)

rating_router.include_router(rating_form_router)

__all__ = ["rating_router"]
