"""Маршруты хайлайтов: веб-страницы и social-действия плюс JSON-лента клиента.

Веб-части разнесены по модулям ``pages``, ``items``, ``social`` и собираются в
``highlight_router`` с префиксом ``/highlights``; лента мобильного клиента живёт в
``feed`` и собирается в ``api_highlights_router`` с префиксом ``/api/v1/highlights``.
Оба роутера объявлены здесь, чтобы порядок подключения путей был виден в одном месте.
"""

from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from backend.presentation.api.v1.highlights.feed import feed_router
from backend.presentation.api.v1.highlights.items import highlight_items_router
from backend.presentation.api.v1.highlights.pages import highlight_pages_router
from backend.presentation.api.v1.highlights.social import highlight_social_router
from backend.presentation.api.version import API_PREFIX

highlight_router = APIRouter(prefix="/highlights", route_class=DishkaRoute)

highlight_router.include_router(highlight_pages_router)
highlight_router.include_router(highlight_items_router)
highlight_router.include_router(highlight_social_router)

api_highlights_router = APIRouter(prefix=f"{API_PREFIX}/highlights", route_class=DishkaRoute)

api_highlights_router.include_router(feed_router)

__all__ = ["api_highlights_router", "highlight_router"]
