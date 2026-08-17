"""Composition facade for highlight routes: pages, items, and social interactions."""

from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from backend.presentation.api.v1.highlight_items_route import highlight_items_router
from backend.presentation.api.v1.highlight_pages_route import highlight_pages_router
from backend.presentation.api.v1.highlight_social_route import highlight_social_router

highlight_router = APIRouter(prefix="/highlights", route_class=DishkaRoute)
highlight_bp = highlight_router

highlight_router.include_router(highlight_pages_router)
highlight_router.include_router(highlight_items_router)
highlight_router.include_router(highlight_social_router)
