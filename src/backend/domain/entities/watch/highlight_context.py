"""Контекст создания хайлайта на странице просмотра."""

from datetime import datetime

from backend.domain.clock import utc_now


class HighlightContext:
    """Данные аниме, серии и таймкода для нового хайлайта."""

    def __init__(
        self,
        highlight_id: int,
        watch_source_id: int,
        translation_id: int,
        title: str = "",
        id: int | None = None,
        created_at: datetime | None = None,
        original_title: str | None = None,
    ):
        """Создать контекст хайлайта."""
        self.id = id
        self.highlight_id = highlight_id
        self.watch_source_id = watch_source_id
        self.translation_id = translation_id
        self.title = title
        self.created_at = created_at or utc_now()
        self.original_title = original_title
