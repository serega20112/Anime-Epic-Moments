"""Auth routes: session, verification, password reset, profile."""

from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from .password_reset import password_reset_router
from .profile import profile_router
from .session import session_router
from .verification import verification_router

auth_router = APIRouter(prefix="/auth", route_class=DishkaRoute)

auth_router.include_router(password_reset_router)
auth_router.include_router(session_router)
auth_router.include_router(verification_router)
auth_router.include_router(profile_router)

__all__ = ["auth_router"]

__all__ = ["auth_router"]
