"""Команды и запросы оценок."""

from __future__ import annotations

from backend.application.dto.rating.get_user_ratings_query import GetUserRatingsQuery
from backend.application.dto.rating.set_user_anime_rating_command import (
    SetUserAnimeRatingCommand,
)

__all__ = ["GetUserRatingsQuery", "SetUserAnimeRatingCommand"]
