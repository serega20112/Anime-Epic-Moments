"""Запрос идентификаторов избранного."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetFavoriteIdsQuery:
    """Запрос идентификаторов избранных аниме.

    Attributes:
        user_id: Идентификатор пользователя.
    """

    user_id: int
