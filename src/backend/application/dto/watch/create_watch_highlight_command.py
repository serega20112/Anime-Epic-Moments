"""Создание хайлайта из плеера вместе с контекстом воспроизведения."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateWatchHighlightCommand:
    """Команда создания хайлайта из плеера.

    Attributes:
        user_id: Идентификатор владельца хайлайта.
        anime_id: Идентификатор аниме.
        episode: Номер серии.
        title: Заголовок хайлайта.
        category: Категория хайлайта.
        start_timestamp: Начало фрагмента в секундах.
        end_timestamp: Конец фрагмента в секундах.
        description: Описание хайлайта.
        is_spoiler: Помечен ли хайлайт как спойлер.
        emotion: Эмоция, выбранная автором.
        watch_source_id: Идентификатор источника воспроизведения.
        translation_id: Идентификатор озвучки.
        original_title: Оригинальное название аниме.
    """

    user_id: int
    anime_id: int
    episode: int | None
    title: str
    category: str | None
    start_timestamp: float | None
    end_timestamp: float | None
    description: str
    is_spoiler: bool
    emotion: str | None
    watch_source_id: int | None
    translation_id: int | None
    original_title: str | None = None
