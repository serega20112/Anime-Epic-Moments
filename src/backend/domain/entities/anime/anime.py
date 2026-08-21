class Anime:
    """Сущность Anime как external reference.

    Не хранит обложки в БД, только URL.
    """

    def __init__(
        self,
        external_id: str,
        title: str,
        description: str | None = None,
        genres: list[str] | None = None,
        year: int | None = None,
        rating: float | None = None,
        cover_url: str | None = None,
        episode_count: int | None = None,
    ):
        self.external_id = external_id  # ID из Jikan/AniList
        self.title = title
        self.description = description
        self.genres = genres or []
        self.year = year
        self.rating = rating
        self.cover_url = cover_url
        self.episode_count = episode_count

    async def add_genre(self, genre: str):
        if genre not in self.genres:
            self.genres.append(genre)

    async def remove_genre(self, genre: str):
        if genre in self.genres:
            self.genres.remove(genre)
