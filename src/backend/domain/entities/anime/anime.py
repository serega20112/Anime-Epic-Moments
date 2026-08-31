class Anime:
    """Сущность Anime как external reference.

    Не хранит обложки в БД, только URL.
    """

    def __init__(
        self,
        external_id: str,
        title: str,
        original_title: str | None = None,
        description: str | None = None,
        genres: list[str] | None = None,
        year: int | None = None,
        rating: float | None = None,
        cover_url: str | None = None,
        episode_count: int | None = None,
    ):
        self.external_id = external_id
        self.title = title
        self.original_title = original_title
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
