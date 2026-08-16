from datetime import datetime


class InvalidHighlightTimeError(Exception):
    pass


class Highlight:
    """Domain entity representing a user-created highlight."""

    def __init__(
        self,
        user_id: int | None,
        anime_id: int,
        episode: int,
        start_timestamp: float,
        end_timestamp: float,
        title: str = "",
        category: str | None = None,
        description: str = "",
        is_spoiler: bool = False,
        emotion: str | None = None,
        created_at: datetime | None = None,
    ):
        self.id: int | None = None
        self.user_id = user_id
        self.anime_id = anime_id
        self.episode = episode
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.title = str(title or "").strip()
        self.category = self._normalize_optional_text(category)
        self.description = description
        self.is_spoiler = is_spoiler
        self.emotion = self._normalize_optional_text(emotion)
        self.likes_count = 0
        self.views_count = 0
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
        title: str,
        category: str | None,
        description: str,
        is_spoiler: bool,
        emotion: str | None = None,
    ):
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.title = str(title or "").strip()
        self.category = self._normalize_optional_text(category)
        self.description = description
        self.is_spoiler = is_spoiler
        self.emotion = self._normalize_optional_text(emotion)
        self._validate_times()

    def add_like(self):
        self.likes_count += 1

    def add_view(self):
        self.views_count += 1

    def _normalize_optional_text(self, value: str | None) -> str | None:
        """Приводит необязательный текст к нормализованному виду или None."""
        text = str(value or "").strip()
        return text or None
