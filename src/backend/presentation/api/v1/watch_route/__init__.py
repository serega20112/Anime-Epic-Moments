"""Тонкие HTTP-маршруты страницы просмотра и действий плеера.

Маршруты разнесены по модулям сценариев плеера: страница, сессии просмотра,
источники, хайлайт из плеера и обсуждение. Сборка единого `watch_router`
остаётся здесь, чтобы порядок подключения путей был виден в одном месте.
"""

from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from backend.presentation.api.v1.watch_route.discussion import discussion_router
from backend.presentation.api.v1.watch_route.highlights import highlights_router
from backend.presentation.api.v1.watch_route.media_proxy import media_proxy_router
from backend.presentation.api.v1.watch_route.page import page_router
from backend.presentation.api.v1.watch_route.sessions import sessions_router
from backend.presentation.api.v1.watch_route.sources import sources_router

watch_router = APIRouter(prefix="/watch", route_class=DishkaRoute)

watch_router.include_router(media_proxy_router)
watch_router.include_router(page_router)
watch_router.include_router(sessions_router)
watch_router.include_router(sources_router)
watch_router.include_router(highlights_router)
watch_router.include_router(discussion_router)

__all__ = ["watch_router"]
