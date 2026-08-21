from datetime import datetime


class UserAnimeStatus:
    def __init__(
        self,
        user_id: int,
        anime_id: int,
        status: str,
        updated_at: datetime | None = None,
        id: int | None = None,
        current_episode: int | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        last_watched_at: datetime | None = None,
        rating: float | None = None,
        note: str | None = None,
    ):
        self.id = id
        self.user_id = user_id
        self.anime_id = anime_id
        self.status = status
        self.updated_at = updated_at or datetime.utcnow()
        self.current_episode = current_episode
        self.started_at = started_at
        self.completed_at = completed_at
        self.last_watched_at = last_watched_at
        self.rating = rating
        self.note = note
