"""Сервис подбора рекомендаций аниме."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from backend.application.interface.repositories.favorite_repository import FavoriteRepository
from backend.application.interface.repositories.highlight_repository import HighlightRepository
from backend.application.interface.services import (
    AnimeApiClientInterface,
    RecommendationCacheInterface,
)
from backend.application.interface.services.recommendation_service import (
    RecommendationServiceInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain import Favorite, Highlight, RecommendationResult
from backend.domain.entities.anime.anime import Anime
from backend.domain.policies.recommendation_policy import (
    score_taste_similarity,
    taste_keywords,
)

CANDIDATE_POOL_SIZE = 40
FALLBACK_POOL_MULTIPLIER = 2
GENRE_REASON = "Похожее на ваши избранные/хайлайты"
POPULAR_REASON = "Популярное среди похожих тайтлов"
TITLE_PREVIEW = "Неизвестное аниме"
DESCRIPTION_PREVIEW = "Описание недоступно"


@dataclass
class _TasteProfile:
    """Срез вкуса пользователя, собранный из избранного и хайлайтов.

    Attributes:
        genres: Жанры избранных тайтлов с частотами.
        keywords: Слова из описаний хайлайтов с частотами.
        anime_cache: Карточки тайтлов, подтянутые из каталога.
        excluded_ids: Идентификаторы, которые предлагать уже нельзя.
        favorite_ids: Идентификаторы избранного в порядке добавления.
        highlight_count: Число хайлайтов автора.
    """

    genres: Counter[str] = field(default_factory=Counter)
    keywords: Counter[str] = field(default_factory=Counter)
    anime_cache: dict[int, Anime | None] = field(default_factory=dict)
    excluded_ids: set[str] = field(default_factory=set)
    favorite_ids: list[int] = field(default_factory=list)
    highlight_count: int = 0


class RecommendationService(RecommendationServiceInterface):
    """Генерация рекомендаций на основе Favorites (жанры) и Highlight descriptions.

    Исключает уже добавленные аниме.
    """

    def __init__(
        self,
        anime_client: AnimeApiClientInterface,
        recommendation_cache: RecommendationCacheInterface,
    ):
        """Собрать сервис рекомендаций из переданных зависимостей.

        Args:
            anime_client: Клиент каталога аниме.
            recommendation_cache: Кэш готовых подборок по пользователям.
        """
        self.anime_client = anime_client
        self.recommendation_cache = recommendation_cache

    async def generate(
        self,
        unit_of_work: UnitOfWorkInterface,
        user_id: int,
        limit: int = 5,
        force_refresh: bool = False,
    ) -> list[RecommendationResult]:
        """Возвращает топ limit рекомендаций для пользователя.

        Args:
            unit_of_work: Граница транзакции чтения избранного и хайлайтов.
            user_id: Идентификатор пользователя.
            limit: Максимальное число рекомендаций.
            force_refresh: Признак сброса кэша и пересчёта подборки.

        Returns:
            list[RecommendationResult]: Рекомендации в порядке убывания похожести.
        """
        if not force_refresh:
            cached = await self.recommendation_cache.get(user_id=user_id, limit=limit)
            if cached is not None:
                return list(cached)

        taste = await self._collect_taste(
            favorites=await unit_of_work.repository(FavoriteRepository).get_by_user(user_id),
            highlights=await unit_of_work.repository(HighlightRepository).get_by_user(user_id),
        )
        if not taste.favorite_ids and not taste.highlight_count:
            await self.recommendation_cache.set(user_id=user_id, limit=limit, value=[])
            return []

        candidates = await self._collect_candidates(taste)
        fresh = [
            anime for anime in candidates if str(anime.external_id or "") not in taste.excluded_ids
        ]
        recommendations = self._rank_by_taste(fresh, taste)
        if recommendations:
            result = recommendations[:limit]
            await self.recommendation_cache.set(user_id=user_id, limit=limit, value=result)
            return list(result)

        fallback = self._rank_by_rating(fresh, limit)
        await self.recommendation_cache.set(user_id=user_id, limit=limit, value=fallback)
        return list(fallback)

    async def invalidate_user(self, user_id: int) -> None:
        """Сбросить рекомендации пользователя после изменения его данных.

        Args:
            user_id: Идентификатор пользователя.
        """
        await self.recommendation_cache.invalidate_user(user_id)

    async def _collect_taste(
        self,
        favorites: list[Favorite],
        highlights: list[Highlight],
    ) -> _TasteProfile:
        """Собрать жанры, слова и список исключений из избранного и хайлайтов.

        Args:
            favorites: Избранные тайтлы пользователя.
            highlights: Хайлайты, созданные пользователем.

        Returns:
            _TasteProfile: Срез вкуса пользователя.
        """
        taste = _TasteProfile()
        taste.favorite_ids = [int(item.anime_id) for item in favorites]
        taste.highlight_count = len(highlights)
        for favorite in favorites:
            taste.excluded_ids.add(str(favorite.anime_id))
            await self._add_genres(favorite.anime_id, favorite.genres, taste)
        for highlight in highlights:
            taste.keywords.update(taste_keywords(highlight.description))
            taste.excluded_ids.add(str(highlight.anime_id))
            await self._anime_of(highlight.anime_id, taste)
        return taste

    async def _add_genres(
        self,
        anime_id: int,
        genres: list[str] | None,
        taste: _TasteProfile,
    ) -> None:
        """Дополнить жанровый профиль: сначала метка избранного, потом каталог.

        Args:
            anime_id: Идентификатор тайтла.
            genres: Жанры, сохранённые вместе с избранным тайтлом.
            taste: Срез вкуса, который обогащается.
        """
        if genres:
            taste.genres.update(genres)
            return
        anime = await self._anime_of(anime_id, taste)
        if anime and anime.genres:
            taste.genres.update(anime.genres)

    async def _anime_of(self, anime_id: int, taste: _TasteProfile) -> Anime | None:
        """Взять карточку тайтла из кэша профиля либо подтянуть её из каталога.

        Args:
            anime_id: Идентификатор тайтла.
            taste: Срез вкуса, хранящий уже загруженные карточки.

        Returns:
            Anime | None: Карточка тайтла либо None, если каталог его не знает.
        """
        if anime_id in taste.anime_cache:
            return taste.anime_cache[anime_id]
        anime = await self.anime_client.get_by_id(anime_id)
        taste.anime_cache[anime_id] = anime
        if anime and str(anime.external_id or "").strip():
            taste.excluded_ids.add(str(anime.external_id).strip())
        return anime

    async def _collect_candidates(self, taste: _TasteProfile) -> list[Anime]:
        """Собрать пул тайтлов, из которых будет строиться подборка.

        Args:
            taste: Срез вкуса пользователя.

        Returns:
            list[Anime]: Кандидаты из топа каталога либо из поиска по избранному.
        """
        candidates = await self.anime_client.get_top_anime(limit=CANDIDATE_POOL_SIZE)
        if candidates:
            return list(candidates)
        return await self._fallback_candidates_from_favorites(taste)

    def _rank_by_taste(
        self,
        candidates: list[Anime],
        taste: _TasteProfile,
    ) -> list[RecommendationResult]:
        """Отранжировать кандидатов по близости к вкусу пользователя.

        Args:
            candidates: Пул тайтлов-кандидатов.
            taste: Срез вкуса пользователя.

        Returns:
            list[RecommendationResult]: Рекомендации с ненулевым весом похожести.
        """
        recommendations: list[RecommendationResult] = []
        for anime in candidates:
            score = score_taste_similarity(
                anime,
                taste_genres=taste.genres,
                keyword_weights=taste.keywords,
            )
            if score <= 0:
                continue
            recommendations.append(self._to_recommendation(anime, score, GENRE_REASON))
        recommendations.sort(key=lambda item: item.similarity_score, reverse=True)
        return recommendations

    def _rank_by_rating(self, candidates: list[Anime], limit: int) -> list[RecommendationResult]:
        """Собрать запасную подборку из самых рейтинговых кандидатов.

        Args:
            candidates: Пул тайтлов-кандидатов.
            limit: Максимальное число рекомендаций.

        Returns:
            list[RecommendationResult]: Рекомендации без учёта сходства текстов.
        """
        ranked = sorted(candidates, key=lambda item: float(item.rating or 0), reverse=True)
        fallback_recommendations: list[RecommendationResult] = []
        for anime in ranked[: max(limit * FALLBACK_POOL_MULTIPLIER, limit)]:
            if int(anime.external_id or 0) <= 0:
                continue
            score = float(anime.rating or 0) / 10
            fallback_recommendations.append(self._to_recommendation(anime, score, POPULAR_REASON))
            if len(fallback_recommendations) >= limit:
                break
        return fallback_recommendations

    @staticmethod
    def _to_recommendation(anime: Anime, score: float, reason: str) -> RecommendationResult:
        """Собрать карточку рекомендации с переходом на страницу просмотра.

        Args:
            anime: Карточка тайтла из каталога.
            score: Итоговый вес похожести.
            reason: Пояснение для пользователя.

        Returns:
            RecommendationResult: Готовая рекомендация.
        """
        anime_id = int(anime.external_id or 0)
        return RecommendationResult(
            anime_id=anime_id,
            reason=reason,
            similarity_score=score,
            title=anime.title or TITLE_PREVIEW,
            description=anime.description or DESCRIPTION_PREVIEW,
            image_url=anime.cover_url,
            genres=anime.genres or [],
            watch_url=f"/watch/{anime_id}?episode=1",
        )

    async def _fallback_candidates_from_favorites(
        self,
        taste: _TasteProfile,
    ) -> list[Anime]:
        """Собрать кандидатов через title-поиск, если top-аниме недоступен.

        Args:
            taste: Срез вкуса пользователя.

        Returns:
            list[Anime]: Найденные по названию тайтлы без повторов.
        """
        merged: list[Anime] = []
        seen: set[str] = set()
        for anime_id in taste.favorite_ids:
            anime = await self._anime_of(anime_id, taste)
            if not anime or not anime.title:
                continue
            for variant in self._title_variants(anime.title):
                found = await self.anime_client.search_by_title(title=variant, limit=12)
                for item in found:
                    key = str(item.external_id or "").strip()
                    if not key or key in seen:
                        continue
                    seen.add(key)
                    merged.append(item)
                    if len(merged) >= CANDIDATE_POOL_SIZE:
                        return merged
        return merged

    @staticmethod
    def _title_variants(title: str) -> list[str]:
        """Подготовить полный и укороченный варианты названия для поиска.

        Args:
            title: Название тайтла.

        Returns:
            list[str]: Варианты поискового запроса.
        """
        variants = [title]
        short_title = " ".join(str(title).split()[:4]).strip()
        if short_title and short_title not in variants:
            variants.append(short_title)
        return variants
