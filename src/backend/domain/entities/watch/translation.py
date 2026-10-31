"""Сущность озвучки серии."""

from datetime import datetime

from backend.domain.clock import utc_now


class Translation:
    """Озвучка, доступная для просмотра, с её плеером."""

    def __init__(
        self,
        anime_id: int,
        name: str,
        translation_type: str,
        language: str = "ru",
        id: int | None = None,
        created_at: datetime | None = None,
    ):
        """Создать озвучку с заданными полями."""
        self.id = id
        self.anime_id = anime_id
        self.name = name
        self.translation_type = translation_type
        self.language = language
        self.created_at = created_at or utc_now()
