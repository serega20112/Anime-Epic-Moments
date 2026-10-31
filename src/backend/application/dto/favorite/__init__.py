"""Команды и запросы избранного."""

from __future__ import annotations

from backend.application.dto.favorite.add_favorite_command import AddFavoriteCommand
from backend.application.dto.favorite.get_favorite_ids_query import GetFavoriteIdsQuery
from backend.application.dto.favorite.get_favorites_query import GetFavoritesQuery
from backend.application.dto.favorite.remove_favorite_command import RemoveFavoriteCommand

__all__ = [
    "AddFavoriteCommand",
    "GetFavoriteIdsQuery",
    "GetFavoritesQuery",
    "RemoveFavoriteCommand",
]
