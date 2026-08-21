from datetime import datetime


class Translation:
    def __init__(
        self,
        anime_id: int,
        name: str,
        translation_type: str,
        language: str = "ru",
        id: int | None = None,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.anime_id = anime_id
        self.name = name
        self.translation_type = translation_type
        self.language = language
        self.created_at = created_at or datetime.utcnow()
