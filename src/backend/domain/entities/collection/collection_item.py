from datetime import datetime


class AnimeCollectionItem:
    """Элемент коллекции аниме со snapshot-метаданными."""

    def __init__(
        self,
        collection_id: int,
        anime_id: int,
        title: str,
        description: str = "",
        cover_url: str | None = None,
        genres: list[str] | None = None,
        added_at: datetime | None = None,
        id: int | None = None,
        original_title: str | None = None,
    ):
        self.id = id
        self.collection_id = int(collection_id)
        self.anime_id = int(anime_id)
        self.title = str(title or "").strip()
        self.description = str(description or "").strip()
        self.cover_url = str(cover_url).strip() if cover_url else None
        self.genres = [str(item).strip() for item in (genres or []) if str(item).strip()]
        self.added_at = added_at or datetime.utcnow()
        self.original_title = str(original_title).strip() if original_title else None
        self._validate()

    def _validate(self):
        if self.anime_id <= 0:
            raise ValueError("anime_id должен быть положительным")
        if not self.title or len(self.title) > 120:
            raise ValueError("Название аниме должно быть от 1 до 120 символов")
