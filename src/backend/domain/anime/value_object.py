from typing import List
from src.backend.domain.anime.entity import Anime


class SearchAnimeByDescriptionResult:
    """Результат поиска аниме по описанию с метаданными age-gate."""

    def __init__(
        self,
        items: List[Anime],
        requires_age_confirmation: bool = False,
        message: str | None = None,
    ):
        self.items = items
        self.requires_age_confirmation = requires_age_confirmation
        self.message = message

    def to_dict(self) -> dict:
        return {
            "items": [vars(item) for item in self.items],
            "requires_age_confirmation": self.requires_age_confirmation,
            "message": self.message,
        }
