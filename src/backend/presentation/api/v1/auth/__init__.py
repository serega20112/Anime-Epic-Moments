"""Маршруты аутентификации: веб-сессия, верификация, сброс пароля, профиль и JSON-API.

Веб-формы (``session``, ``verification``, ``password_reset``, ``profile``)
собираются в ``auth_router`` с префиксом ``/auth``, а JSON-поверхность мобильного
клиента (``token``, ``google``) — в ``api_auth_router`` с префиксом
``/api/v1/auth``. Оба роутера объявлены здесь, чтобы порядок подключения путей
был виден в одном месте.
"""

from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from backend.presentation.api.v1.auth.google import google_router
from backend.presentation.api.v1.auth.password_reset import password_reset_router
from backend.presentation.api.v1.auth.profile import profile_router
from backend.presentation.api.v1.auth.session import session_router
from backend.presentation.api.v1.auth.token import token_router
from backend.presentation.api.v1.auth.verification import verification_router
from backend.presentation.api.version import API_PREFIX

auth_router = APIRouter(prefix="/auth", route_class=DishkaRoute)

auth_router.include_router(password_reset_router)
auth_router.include_router(session_router)
auth_router.include_router(verification_router)
auth_router.include_router(profile_router)

api_auth_router = APIRouter(prefix=f"{API_PREFIX}/auth", route_class=DishkaRoute)

api_auth_router.include_router(token_router)
api_auth_router.include_router(google_router)


__all__ = ["api_auth_router", "auth_router"]
