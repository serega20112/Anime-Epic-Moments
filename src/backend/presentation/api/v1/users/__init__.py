"""JSON-маршруты пользователя мобильного клиента: профиль, библиотека, аккаунт.

Функции разнесены по модулям сценариев (``profile``, ``library``, ``account``),
единый ``api_users_router`` с префиксом собирается здесь, чтобы порядок
подключения путей был виден в одном месте. Публичный профиль доступен гостю,
остальные маршруты приватны и сверяют идентификатор из пути с сессией.
"""

from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from backend.presentation.api.v1.users.account import account_router
from backend.presentation.api.v1.users.library import library_router
from backend.presentation.api.v1.users.profile import profile_router
from backend.presentation.api.v1.users.web import user_router
from backend.presentation.api.version import API_PREFIX

api_users_router = APIRouter(prefix=f"{API_PREFIX}/users", route_class=DishkaRoute)

api_users_router.include_router(profile_router)
api_users_router.include_router(library_router)
api_users_router.include_router(account_router)

__all__ = ["api_users_router", "user_router"]
