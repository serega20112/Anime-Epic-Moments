from __future__ import annotations

from collections import Counter

from src.backend.domain.recommendation.value_object import RecommendationResult
from src.backend.infrastructure.external.anime_api_client import AnimeApiClient
from src.backend.infrastructure.external.huggingface_llm_client import HuggingFaceLLMClient
from src.backend.repository.favorite_repository import FavoriteRepository


class AskAiRecommendationsUseCase:
    """Подбирает рекомендации по свободному текстовому запросу пользователя."""

    def __init__(
        self,
        favorite_repo: FavoriteRepository,
        anime_api_client: AnimeApiClient,
        hf_llm_client: HuggingFaceLLMClient,
    ):
        self.favorite_repo = favorite_repo
        self.anime_api_client = anime_api_client
        self.hf_llm_client = hf_llm_client

    def execute(
        self,
        user_id: int,
        query: str,
        limit: int = 6,
    ) -> list[RecommendationResult]:
        normalized_query = str(query or "").strip()
        if not normalized_query:
            return []

        favorites = self.favorite_repo.get_by_user(user_id)
        genre_hint = self._build_genre_hint(favorites)
        queries, mode, _error = self.hf_llm_client.build_search_queries_with_meta(
            description=normalized_query,
            genre_hint=genre_hint,
        )
        if not queries:
            return []

        existing_ids = {int(item.anime_id) for item in favorites}
        seen: set[int] = set()
        recommendations: list[RecommendationResult] = []
        top_genres = Counter(
            genre
            for favorite in favorites
            for genre in (favorite.genres or [])
        )

        for index, generated_query in enumerate(queries):
            candidates = self.anime_api_client.search_by_description(
                description=generated_query,
                limit=max(limit * 2, 8),
            )
            if not candidates:
                candidates = self.anime_api_client.search_by_title(
                    title=generated_query,
                    limit=max(limit * 2, 8),
                )
            for anime in candidates:
                anime_id = int(anime.external_id or 0)
                if anime_id <= 0 or anime_id in existing_ids or anime_id in seen:
                    continue
                seen.add(anime_id)
                genre_overlap = len(
                    set(anime.genres or []) & set(top_genres.keys())
                )
                score = (
                    max(0.0, 1.0 - index * 0.1)
                    + genre_overlap * 0.35
                    + float(anime.rating or 0) / 10
                )
                recommendations.append(
                    RecommendationResult(
                        anime_id=anime_id,
                        reason=self._build_reason(
                            prompt=normalized_query,
                            anime_title=anime.title or f"Anime #{anime_id}",
                            genres=anime.genres or [],
                            mode=mode,
                        ),
                        similarity_score=round(score, 3),
                        title=anime.title or f"Anime #{anime_id}",
                        description=anime.description or "Описание недоступно",
                        image_url=anime.cover_url,
                        genres=anime.genres or [],
                        watch_url=f"/watch/{anime_id}?episode=1",
                    )
                )
        recommendations.sort(key=lambda item: item.similarity_score, reverse=True)
        return recommendations[: max(int(limit), 1)]

    def _build_genre_hint(self, favorites) -> str | None:
        counter = Counter(
            genre
            for favorite in favorites
            for genre in (favorite.genres or [])
            if str(genre).strip()
        )
        if not counter:
            return None
        return ", ".join(name for name, _count in counter.most_common(3))

    def _build_reason(
        self,
        prompt: str,
        anime_title: str,
        genres: list[str],
        mode: str,
    ) -> str:
        genre_part = f" Жанровый профиль: {', '.join(genres[:3])}." if genres else ""
        mode_part = " Запрос разобран через AI." if mode == "hf_llm_text" else ""
        return (
            f"Подборка под запрос «{prompt}». {anime_title} совпадает по тону и жанровому профилю."
            f"{genre_part}{mode_part}"
        ).strip()
