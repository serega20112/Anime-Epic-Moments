from datetime import datetime


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
        id: int | None = None,
        created_at: datetime | None = None,
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
