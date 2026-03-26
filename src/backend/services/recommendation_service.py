from typing import List
from collections import Counter
from src.backend.domain.recommendation.value_object import RecommendationResult
from src.backend.repository.favorite_repository import FavoriteRepository
from src.backend.repository.highlight_repository import HighlightRepository
from src.backend.infrastructure.external.anime_api_client import AnimeApiClient


class RecommendationService:
    """
    Генерация рекомендаций на основе:
    - Favorites (жанры)
    - Highlight descriptions (ключевые слова)
    Исключает уже добавленные аниме.
    """

    def __init__(
        self,
        fav_repo: FavoriteRepository,
        highlight_repo: HighlightRepository,
        anime_client: AnimeApiClient,
    ):
        self.fav_repo = fav_repo
        self.highlight_repo = highlight_repo
        self.anime_client = anime_client

    def generate(self, user_id: int, limit: int = 5) -> List[RecommendationResult]:
        """
        Возвращает топ limit рекомендаций для пользователя
        """
        favorites = self.fav_repo.get_by_user(user_id)
        highlights = self.highlight_repo.get_by_user(user_id)

        if not favorites and not highlights:
            return []

        # Собираем все жанры из избранного
        fav_genres = []
        for fav in favorites:
            anime = self.anime_client.get_by_id(fav.anime_id)
            if anime and anime.genres:
                fav_genres.extend(anime.genres)

        genre_counter = Counter(fav_genres)

        # Собираем ключевые слова из описаний хайлайтов
        keywords = []
        for hl in highlights:
            keywords.extend(hl.description.lower().split())

        keyword_counter = Counter(keywords)

        # Получаем похожие аниме через API по жанрам и ключевым словам
        candidate_anime = self.anime_client.get_top_anime(limit=40)

        # Убираем уже добавленные
        existing_ids = {str(fav.anime_id) for fav in favorites}
        existing_ids.update({str(hl.anime_id) for hl in highlights})
        candidate_anime = [
            anime for anime in candidate_anime
            if str(anime.external_id or "") not in existing_ids
        ]

        # Вычисляем score
        recommendations = []
        for anime in candidate_anime:
            anime_genres = anime.genres or []
            anime_text = f"{anime.title or ''} {anime.description or ''}".lower()
            genre_overlap = len(set(anime_genres) & set(genre_counter.keys()))
            keyword_overlap = sum(
                weight for key, weight in keyword_counter.items()
                if len(key) > 3 and key in anime_text
            )
            rating_weight = (anime.rating or 0) / 10

            score = genre_overlap * 0.6 + keyword_overlap * 0.3 + rating_weight * 0.1
            if score <= 0:
                continue
            recommendations.append(
                RecommendationResult(
                    anime_id=int(anime.external_id or 0),
                    reason="Похожее на ваши избранные/хайлайты",
                    similarity_score=score,
                    title=anime.title or "Неизвестное аниме",
                    description=anime.description or "Описание недоступно",
                    image_url=anime.cover_url,
                    genres=anime_genres,
                    watch_url=f"/watch/{anime.external_id or 0}?episode=1",
                )
            )

        # Сортируем по score
        recommendations.sort(key=lambda r: r.similarity_score, reverse=True)

        return recommendations[:limit]
