from datetime import datetime


class Favorite:
    def __init__(
        self,
        user_id: int,
        anime_id: int,
        added_at: datetime = None,
        title: str | None = None,
        description: str | None = None,
        cover_url: str | None = None,
        genres: list[str] | None = None,
    ):
        self.user_id = user_id
        self.anime_id = anime_id
        self.added_at = added_at or datetime.utcnow()
        self.title = title
        self.description = description
        self.cover_url = cover_url
        self.genres = genres or []
