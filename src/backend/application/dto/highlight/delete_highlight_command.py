"""Команда удаления хайлайта."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeleteHighlightCommand:
    """Команда удаления хайлайта.

    Attributes:
        highlight_id: Идентификатор хайлайта.
        user_id: Идентификатор автора; только он вправе удалить хайлайт.
    """

    highlight_id: int
    user_id: int
