"""Сущность избранного аниме."""

from datetime import datetime

from backend.domain.clock import utc_now


class Favorite:
    """Отметка аниме в избранном пользователя."""

    def __init__(
        self,
        user_id: int,
        anime_id: int,
        added_at: datetime | None = None,
        title: str | None = None,
        description: str | None = None,
        cover_url: str | None = None,
        genres: list[str] | None = None,
        original_title: str | None = None,
    ):
        """Создать отметку избранного."""
        self.user_id = user_id
        self.anime_id = anime_id
        self.added_at = added_at or utc_now()
        self.title = title
        self.description = description
        self.cover_url = cover_url
        self.genres = genres or []
        self.original_title = original_title
