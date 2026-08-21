from datetime import datetime


class ViewingSession:
    def __init__(
        self,
        user_id: int,
        anime_id: int,
        episode: int,
        watch_source_id: int,
        position_seconds: float,
        volume: float,
        quality_label: str,
        is_paused: bool,
        id: int | None = None,
        updated_at: datetime | None = None,
    ):
        self.id = id
        self.user_id = user_id
        self.anime_id = anime_id
        self.episode = episode
        self.watch_source_id = watch_source_id
        self.position_seconds = position_seconds
        self.volume = volume
        self.quality_label = quality_label
        self.is_paused = is_paused
        self.updated_at = updated_at or datetime.utcnow()
