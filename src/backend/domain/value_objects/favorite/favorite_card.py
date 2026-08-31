from dataclasses import dataclass


@dataclass
class FavoriteAnimeCard:
    anime_id: int
    title: str
    description: str
    cover_url: str | None
    genres: list[str]
    watch_url: str
    added_at: str
    original_title: str | None = None
