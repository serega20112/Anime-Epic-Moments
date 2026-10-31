"""Модели ответов избранного."""

from __future__ import annotations

from pydantic import BaseModel


class FavoriteIdsResponse(BaseModel):
    """Ответ со списком идентификаторов избранного.

    Attributes:
        user_id: Идентификатор владельца избранного.
        anime_ids: Идентификаторы избранных аниме.
    """

    user_id: int
    anime_ids: list[int]
