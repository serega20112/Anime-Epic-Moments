"""Команда редактирования хайлайта."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EditHighlightCommand:
    """Команда редактирования хайлайта.

    Attributes:
        highlight_id: Идентификатор хайлайта.
        user_id: Идентификатор автора; только он вправе изменить хайлайт.
        episode: Номер серии, None оставляет прежний.
        start_timestamp: Начало момента в секундах.
        end_timestamp: Конец момента в секундах.
        title: Название хайлайта.
        category: Необязательная категория.
        description: Описание хайлайта.
        is_spoiler: Содержит ли хайлайт спойлеры.
        emotion: Необязательная метка эмоции.
    """

    highlight_id: int
    user_id: int
    episode: int | None
    start_timestamp: float
    end_timestamp: float
    title: str
    category: str | None
    description: str
    is_spoiler: bool
    emotion: str | None = None
