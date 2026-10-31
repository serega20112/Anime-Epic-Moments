"""Сущности моментов просмотра."""

from __future__ import annotations

from datetime import datetime

from backend.domain.clock import utc_now


class ViewingMoment:
    """Черновик хайлайта, снятый на моменте воспроизведения."""

    def __init__(
        self,
        user_id: int,
        anime_id: int,
        episode: int,
        timestamp: float,
        watch_source_id: int | None = None,
        caption: str | None = None,
        sticker: str | None = None,
        screenshot_url: str | None = None,
        id: int | None = None,
        created_at: datetime | None = None,
    ):
        """Создать черновик момента с заданными полями."""
        self.id = id
        self.user_id = user_id
        self.anime_id = anime_id
        self.episode = episode
        self.timestamp = timestamp
        self.watch_source_id = watch_source_id
        self.caption = caption
        self.sticker = sticker
        self.screenshot_url = screenshot_url
        self.created_at = created_at or utc_now()
