from typing import List
from collections import Counter
from src.backend.domain.recommendation.value_object import RecommendationResult
from src.backend.domain.anime.entity import Anime
from src.backend.infrastructure.cache.recommendation_cache import RecommendationCache
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
        recommendation_cache: RecommendationCache,
    ):
        self.fav_repo = fav_repo
        self.highlight_repo = highlight_repo
        self.anime_client = anime_client
        self.recommendation_cache = recommendation_cache

    def generate(
        self, user_id: int, limit: int = 5, force_refresh: bool = False
    ) -> List[RecommendationResult]:
        """
        Возвращает топ limit рекомендаций для пользователя
        """
        if not force_refresh:
            cached = self.recommendation_cache.get(user_id=user_id, limit=limit)
            if cached is not None:
                return list(cached)

        favorites = self.fav_repo.get_by_user(user_id)
        highlights = self.highlight_repo.get_by_user(user_id)

        if not favorites and not highlights:
            self.recommendation_cache.set(user_id=user_id, limit=limit, value=[])
            return []

        # Собираем все жанры из избранного
        fav_genres = []
        anime_cache: dict[int, Anime | None] = {}
        for fav in favorites:
            if fav.genres:
                fav_genres.extend(fav.genres)
                continue
            anime = self.anime_client.get_by_id(fav.anime_id)
            anime_cache[fav.anime_id] = anime
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
        if not candidate_anime:
            candidate_anime = self._fallback_candidates_from_favorites(favorites, limit=40)

        # Убираем уже добавленные
        existing_ids = {str(fav.anime_id) for fav in favorites}
        existing_ids.update({str(hl.anime_id) for hl in highlights})
        existing_ids.update(
            {
                str(anime.external_id).strip()
                for anime in anime_cache.values()
                if anime and str(anime.external_id or "").strip()
            }
        )
        for highlight in highlights:
            anime = anime_cache.get(highlight.anime_id)
            if anime is None and highlight.anime_id not in anime_cache:
                anime = self.anime_client.get_by_id(highlight.anime_id)
                anime_cache[highlight.anime_id] = anime
            if anime and str(anime.external_id or "").strip():
                existing_ids.add(str(anime.external_id).strip())
        candidate_anime = [
            anime
            for anime in candidate_anime
            if str(anime.external_id or "") not in existing_ids
        ]

        # Вычисляем score
        recommendations = []
        for anime in candidate_anime:
            anime_genres = anime.genres or []
            anime_text = f"{anime.title or ''} {anime.description or ''}".lower()
            genre_overlap = len(set(anime_genres) & set(genre_counter.keys()))
            keyword_overlap = sum(
                weight
                for key, weight in keyword_counter.items()
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

        if recommendations:
            result = recommendations[:limit]
            self.recommendation_cache.set(user_id=user_id, limit=limit, value=result)
            return list(result)

        # Fallback: чтобы блок рекомендаций не был пустым при деградации API/данных
        fallback_items = sorted(
            candidate_anime,
            key=lambda item: float(item.rating or 0),
            reverse=True,
        )
        fallback_recommendations: List[RecommendationResult] = []
        for anime in fallback_items[: max(limit * 2, limit)]:
            anime_id = int(anime.external_id or 0)
            if anime_id <= 0:
                continue
            fallback_recommendations.append(
                RecommendationResult(
                    anime_id=anime_id,
                    reason="Популярное среди похожих тайтлов",
                    similarity_score=float(anime.rating or 0) / 10,
                    title=anime.title or "Неизвестное аниме",
                    description=anime.description or "Описание недоступно",
                    image_url=anime.cover_url,
                    genres=anime.genres or [],
                    watch_url=f"/watch/{anime_id}?episode=1",
                )
            )
            if len(fallback_recommendations) >= limit:
                break
        self.recommendation_cache.set(
            user_id=user_id,
            limit=limit,
            value=fallback_recommendations,
        )
        return list(fallback_recommendations)

    def invalidate_user(self, user_id: int):
        self.recommendation_cache.invalidate_user(user_id)

    def _fallback_candidates_from_favorites(
        self, favorites, limit: int = 40
    ) -> List[Anime]:
        """Собирает кандидатов через title-поиск, если top-аниме недоступен."""
        merged: List[Anime] = []
        seen: set[str] = set()

        for favorite in favorites:
            anime = self.anime_client.get_by_id(favorite.anime_id)
            if not anime or not anime.title:
                continue
            variants = [anime.title]
            short_title = " ".join(str(anime.title).split()[:4]).strip()
            if short_title and short_title not in variants:
                variants.append(short_title)

            for variant in variants:
                found = self.anime_client.search_by_title(title=variant, limit=12)
                for item in found:
                    key = str(item.external_id or "").strip()
                    if not key or key in seen:
                        continue
                    seen.add(key)
                    merged.append(item)
                    if len(merged) >= limit:
                        return merged
        return merged
