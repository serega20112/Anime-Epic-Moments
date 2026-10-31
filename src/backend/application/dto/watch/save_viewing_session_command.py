"""Сохранение позиции сессии просмотра."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SaveViewingSessionCommand:
    """Команда сохранения состояния плеера.

    Attributes:
        user_id: Идентификатор действующего пользователя.
        anime_id: Идентификатор аниме.
        episode: Номер серии.
        watch_source_id: Идентификатор источника воспроизведения.
        position_seconds: Текущая позиция в секундах.
        volume: Уровень громкости.
        quality_label: Выбранное качество.
        is_paused: Приостановлено ли воспроизведение.
    """

    user_id: int
    anime_id: int
    episode: int | None
    watch_source_id: int | None
    position_seconds: float = 0.0
    volume: float = 1.0
    quality_label: str = "Auto"
    is_paused: bool = False
