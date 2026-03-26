from dataclasses import dataclass
from typing import List


@dataclass
class FavoriteAnimeCard:
    anime_id: int
    title: str
    description: str
    cover_url: str | None
    genres: List[str]
    watch_url: str
    added_at: str
