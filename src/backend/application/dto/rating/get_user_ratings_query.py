"""Запрос оценок аниме пользователя."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetUserRatingsQuery:
    """Запрос оценок пользователя по аниме.

    Attributes:
        user_id: Идентификатор пользователя.
    """

    user_id: int
