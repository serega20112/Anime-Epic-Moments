"""Параметры публичной карточки одного хайлайта."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HighlightSharedQuery:
    """Запрос карточки хайлайта по публичной ссылке.

    Attributes:
        highlight_id: Идентификатор хайлайта.
        viewer_user_id: Идентификатор зрителя для отметок лайков и сохранений.
    """

    highlight_id: int
    viewer_user_id: int | None = None
