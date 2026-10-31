"""Параметры синхронизации источников просмотра."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SyncWatchSourcesQuery:
    """Запрос поиска источников у внешнего провайдера.

    Attributes:
        anime_id: Идентификатор аниме.
        episode: Номер серии.
        force: Принудительно обновить кэш провайдеров.
    """

    anime_id: int
    episode: int
    force: bool = False
