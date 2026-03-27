class RecommendationResult:
    def __init__(
        self,
        anime_id: int,
        reason: str,
        similarity_score: float,
        title: str,
        description: str,
        image_url: str | None,
        genres: list[str] | None = None,
        watch_url: str | None = None,
    ):
        self.anime_id = anime_id
        self.reason = reason
        self.similarity_score = similarity_score
        self.title = title
        self.description = description
        self.image_url = image_url
        self.genres = genres or []
        self.watch_url = watch_url
