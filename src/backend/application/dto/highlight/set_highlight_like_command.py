"""Постановка и снятие лайка хайлайту."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SetHighlightLikeCommand:
    """Команда изменения лайка хайлайта.

    Attributes:
        highlight_id: Идентификатор хайлайта.
        user_id: Идентификатор действующего пользователя.
        liked: True — поставить лайк, False — снять.
    """

    highlight_id: int
    user_id: int
    liked: bool
