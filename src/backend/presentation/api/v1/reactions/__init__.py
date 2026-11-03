"""Маршруты реакций на серии.

Функции живут в модуле ``episode_reactions``, а ``reaction_router`` с префиксом
``/watch`` объявляется здесь: реакции относятся к странице просмотра.
"""

from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from backend.presentation.api.v1.reactions.episode_reactions import (
    episode_reactions_router,
)

reaction_router = APIRouter(prefix="/watch", route_class=DishkaRoute)

reaction_router.include_router(episode_reactions_router)

__all__ = ["reaction_router"]
