"""Создание хайлайта из формы."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateHighlightCommand:
    """Команда создания хайлайта.

    Attributes:
        user_id: Идентификатор владельца либо None для гостя.
        anime_id: Идентификатор аниме.
        episode: Номер серии.
        start_timestamp: Начало фрагмента в секундах.
        end_timestamp: Конец фрагмента в секундах.
        title: Заголовок хайлайта.
        category: Категория хайлайта.
        description: Описание хайлайта.
        is_spoiler: Помечен ли хайлайт как спойлер.
        emotion: Эмоция, выбранная автором.
        highlights_this_hour: Сколько хайлайтов пользователь уже создал за час.
    """

    user_id: int | None
    anime_id: int
    episode: int
    start_timestamp: float
    end_timestamp: float
    title: str = ""
    category: str | None = None
    description: str = ""
    is_spoiler: bool = False
    emotion: str | None = None
    highlights_this_hour: int = 0
