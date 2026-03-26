from datetime import datetime
from typing import Optional


class InvalidHighlightTimeError(Exception):
    pass


class Highlight:
    """
    Агрегат Highlight
    """

    def __init__(
        self,
        user_id: Optional[int],
        anime_id: int,
        episode: int,
        start_timestamp: float,
        end_timestamp: float,
        description: str = "",
        is_spoiler: bool = False,
        emotion: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id: Optional[int] = None
        self.user_id = user_id
        self.anime_id = anime_id
        self.episode = episode
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.description = description
        self.is_spoiler = is_spoiler
        self.emotion = emotion
        self.likes_count = 0
        self.created_at = created_at or datetime.utcnow()

        self._validate_times()

    def _validate_times(self):
        if self.start_timestamp >= self.end_timestamp:
            raise InvalidHighlightTimeError(
                f"start_timestamp ({self.start_timestamp}) должен быть меньше end_timestamp ({self.end_timestamp})"
            )

    def edit(
        self,
        start_timestamp: float,
        end_timestamp: float,
        description: str,
        is_spoiler: bool,
    ):
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.description = description
        self.is_spoiler = is_spoiler
        self._validate_times()

    def add_like(self):
        self.likes_count += 1

    def remove_like(self):
        if self.likes_count > 0:
            self.likes_count -= 1
