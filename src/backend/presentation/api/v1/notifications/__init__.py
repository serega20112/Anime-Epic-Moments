"""JSON-маршруты центра уведомлений мобильного клиента.

Функции разнесены по модулям сценариев (``feed``, ``actions``), единый
``api_notifications_router`` собирается здесь. Префикс ``/api/v1/notifications``
несут дочерние роутеры, а не родитель: корневой ``GET`` ленты объявлен пустым
путём, который FastAPI не допускает на роутере без префикса. Видимая область —
уведомления пользователя сессии: идентификатор берётся из аутентификации, а не
из пути, поэтому чужие уведомления недоступны по подставному id. Выборку и
отметки-read выполняют сценарии; маршрут лишь разбирает параметры и собирает
ответ.
"""

from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from backend.presentation.api.v1.notifications.actions import actions_router
from backend.presentation.api.v1.notifications.feed import feed_router

api_notifications_router = APIRouter(route_class=DishkaRoute)

api_notifications_router.include_router(feed_router)
api_notifications_router.include_router(actions_router)

__all__ = ["api_notifications_router"]
