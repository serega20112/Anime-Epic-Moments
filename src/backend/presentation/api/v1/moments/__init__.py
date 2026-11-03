"""Маршруты моментов просмотра и их черновиков.

Черновик из плеера живёт в модуле ``player`` (роутер ``/watch``), список,
публикация и удаление — в ``drafts`` (роутер ``/moments``). Оба роутера несут
свои префиксы и подключаются здесь: у списка черновиков пустой путь, поэтому
объединять их под общим родителем без префикса нельзя.
"""

from __future__ import annotations

from backend.presentation.api.v1.moments.drafts import moment_router
from backend.presentation.api.v1.moments.player import watch_moment_router

__all__ = ["moment_router", "watch_moment_router"]
