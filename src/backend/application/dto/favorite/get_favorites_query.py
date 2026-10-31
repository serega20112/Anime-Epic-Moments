"""Запрос списка избранного."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetFavoritesQuery:
    """Запрос карточек избранного пользователя.

    Attributes:
        user_id: Идентификатор пользователя.
    """

    user_id: int
