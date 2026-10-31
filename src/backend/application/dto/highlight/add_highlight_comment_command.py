"""Добавление комментария к хайлайту."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AddHighlightCommentCommand:
    """Команда добавления комментария к хайлайту.

    Attributes:
        highlight_id: Идентификатор хайлайта.
        user_id: Идентификатор автора комментария.
        content: Текст комментария.
    """

    highlight_id: int
    user_id: int
    content: str
