from __future__ import annotations

from datetime import datetime


class AnimeCollection:
    """Агрегат пользовательской коллекции аниме."""

    def __init__(
        self,
        user_id: int,
        title: str,
        description: str = "",
        is_public: bool = True,
        cover_url: str | None = None,
        created_at: datetime | None = None,
        id: int | None = None,
    ):
        self.id = id
        self.user_id = int(user_id)
        self.title = str(title or "").strip()
        self.description = str(description or "").strip()
        self.is_public = bool(is_public)
        self.cover_url = str(cover_url).strip() if cover_url else None
        self.created_at = created_at or datetime.utcnow()
        self._validate()

    def _validate(self):
        if not self.title or len(self.title) > 80:
            raise ValueError("Название коллекции должно быть от 1 до 80 символов")
        if len(self.description) > 400:
            raise ValueError("Описание коллекции не должно превышать 400 символов")
