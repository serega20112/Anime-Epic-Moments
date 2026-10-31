"""Удаление аниме из избранного."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RemoveFavoriteCommand:
    """Команда удаления аниме из избранного.

    Attributes:
        user_id: Идентификатор пользователя, чьё избранное меняется.
        anime_id: Идентификатор аниме.
    """

    user_id: int
    anime_id: int
