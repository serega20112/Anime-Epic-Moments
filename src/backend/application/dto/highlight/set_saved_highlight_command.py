"""Сохранение хайлайта и удаление его из сохранённых."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SetSavedHighlightCommand:
    """Команда изменения отметки «сохранён».

    Attributes:
        highlight_id: Идентификатор хайлайта.
        user_id: Идентификатор действующего пользователя.
        saved: True — сохранить, False — убрать из сохранённых.
    """

    highlight_id: int
    user_id: int
    saved: bool
