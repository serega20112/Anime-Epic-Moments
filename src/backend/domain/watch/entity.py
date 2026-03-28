from datetime import datetime
from typing import Optional


class UserAnimeStatus:
    def __init__(
        self,
        user_id: int,
        anime_id: int,
        status: str,
        updated_at: Optional[datetime] = None,
        id: Optional[int] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.anime_id = anime_id
        self.status = status
        self.updated_at = updated_at or datetime.utcnow()


class Translation:
    def __init__(
        self,
        anime_id: int,
        name: str,
        translation_type: str,
        language: str = "ru",
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.anime_id = anime_id
        self.name = name
        self.translation_type = translation_type
        self.language = language
        self.created_at = created_at or datetime.utcnow()


class WatchSource:
    def __init__(
        self,
        anime_id: int,
        episode: int,
        translation_id: int,
        provider_name: str,
        source_name: str,
        stream_url: str,
        quality_label: str,
        source_type: str = "stream",
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.anime_id = anime_id
        self.episode = episode
        self.translation_id = translation_id
        self.provider_name = provider_name
        self.source_name = source_name
        self.stream_url = stream_url
        self.quality_label = quality_label
        self.source_type = source_type
        self.created_at = created_at or datetime.utcnow()


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
        id: Optional[int] = None,
        updated_at: Optional[datetime] = None,
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


class HighlightContext:
    def __init__(
        self,
        highlight_id: int,
        watch_source_id: int,
        translation_id: int,
        title: str = "",
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.highlight_id = highlight_id
        self.watch_source_id = watch_source_id
        self.translation_id = translation_id
        self.title = title
        self.created_at = created_at or datetime.utcnow()
