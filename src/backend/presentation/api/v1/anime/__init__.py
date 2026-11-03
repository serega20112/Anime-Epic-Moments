"""JSON- и веб-маршруты тайтла: карточка, прогресс, поиск и каталог.

Веб-страницы и JSON-API каталога живут в модуле ``web``, карточка и прогресс
мобильного клиента — в ``detail`` и ``progress``. Здесь собираются два роутера:
``anime_router`` с префиксом ``/anime`` и ``api_anime_router`` с префиксом
``/api/v1/anime``. Карточка отдаётся сценарием детализации поверх страницы
просмотра, позиция пишется тем же сценарием сохранения сессии, что и веб-плеер,
поэтому правила серий, источников и порога «просмотрено» не дублируются.
"""

from __future__ import annotations

from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from backend.presentation.api.v1.anime.detail import detail_router
from backend.presentation.api.v1.anime.progress import progress_router
from backend.presentation.api.v1.anime.web import web_router
from backend.presentation.api.version import API_PREFIX

anime_router = APIRouter(prefix="/anime", route_class=DishkaRoute)
anime_router.include_router(web_router)

api_anime_router = APIRouter(prefix=f"{API_PREFIX}/anime", route_class=DishkaRoute)

api_anime_router.include_router(detail_router)
api_anime_router.include_router(progress_router)

__all__ = ["anime_router", "api_anime_router"]
