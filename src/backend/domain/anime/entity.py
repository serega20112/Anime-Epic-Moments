from typing import List, Optional


class Anime:
    """
    Сущность Anime как external reference.
    Не хранит обложки в БД, только URL.
    """

    def __init__(
        self,
        external_id: str,
        title: str,
        description: Optional[str] = None,
        genres: Optional[List[str]] = None,
        year: Optional[int] = None,
        rating: Optional[float] = None,
        cover_url: Optional[str] = None,
        episode_count: Optional[int] = None,
    ):
        self.external_id = external_id  # ID из Jikan/AniList
        self.title = title
        self.description = description
        self.genres = genres or []
        self.year = year
        self.rating = rating
        self.cover_url = cover_url
        self.episode_count = episode_count

    def add_genre(self, genre: str):
        if genre not in self.genres:
            self.genres.append(genre)

    def remove_genre(self, genre: str):
        if genre in self.genres:
            self.genres.remove(genre)
