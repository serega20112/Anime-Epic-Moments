"""Репозиторий просмотра: прогресс, источники, сессии, аналитика и обсуждение.

Класс собирается из mixin'ов по агрегатам — каждый модуль пакета отвечает за свою
группу таблиц и не лезет в чужую:

- `progress` — дневник пользователя (`user_anime_statuses`);
- `sources` — переводы и playable-источники (`translations`, `watch_sources`);
- `sessions` — позиции плеера и контексты хайлайтов (`viewing_sessions`,
  `highlight_contexts`);
- `analytics` — агрегаты для витрины профиля;
- `discussion` — комментарии обсуждения и лайки к ним.

Наружу отдаётся только `WatchRepository`: потребители импортируют пакет, а не его
внутренние модули, поэтому дальнейшее дробление ничего не ломает.
"""

from __future__ import annotations

from .watch import WatchRepository

__all__ = ["WatchRepository"]
