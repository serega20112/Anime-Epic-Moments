"""Сценарий подбора рекомендаций через ИИ.

Оркестрация: прочитать избранное, расширить запрос моделью, собрать кандидатов
из каталога и выдать готовую подборку. Правила того, что считать похожим
тайтлом, живут в :mod:`backend.domain.policies.recommendation_policy`.
"""

from __future__ import annotations

from collections import Counter

from starlette import status

from backend.application.dto import AskAiRecommendationsCommand
from backend.application.interface.repositories.favorite_repository import FavoriteRepository
from backend.application.interface.services import AnimeApiClientInterface, LLMClientInterface
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult
from backend.domain import Favorite, RecommendationResult
from backend.domain.entities.anime.anime import Anime
from backend.domain.policies.recommendation_lexicon import (
    extract_subject_terms,
    extract_terms,
)
from backend.domain.policies.recommendation_policy import (
    build_recommendation,
    build_search_plan,
    finalize_recommendations,
    score_candidate,
    search_limit_for,
)
from backend.domain.value_objects.recommendation.candidate_score import CandidateScore


class AskAiRecommendationsUseCase:
    """Подбирает рекомендации по свободному текстовому запросу пользователя."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        anime_api_client: AnimeApiClientInterface,
        hf_llm_client: LLMClientInterface,
    ) -> None:
        """Собрать сценарий ИИ-рекомендаций.

        Args:
            unit_of_work: Граница транзакции чтения избранного пользователя.
            anime_api_client: Клиент каталога аниме.
            hf_llm_client: Клиент LLM для разбора запроса.
        """
        self._unit_of_work = unit_of_work
        self._anime_api_client = anime_api_client
        self._hf_llm_client = hf_llm_client

    async def execute(
        self,
        command: AskAiRecommendationsCommand,
    ) -> UseCaseResult:
        """Подобрать рекомендации по свободному запросу.

        Args:
            command: Запрос пользователя, идентификатор и лимит выдачи.

        Returns:
            UseCaseResult: Список рекомендаций либо ошибка пустого запроса.
        """
        normalized_query = str(command.query or "").strip()
        if not normalized_query:
            return UseCaseResult.failure(
                "invalid_query",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return UseCaseResult.success(
            await self._build_recommendations(
                user_id=command.user_id,
                normalized_query=normalized_query,
                limit=command.limit,
            )
        )

    async def _build_recommendations(
        self,
        user_id: int,
        normalized_query: str,
        limit: int,
    ) -> list[RecommendationResult]:
        """Собрать рекомендации из избранного и ответов модели.

        Args:
            user_id: Идентификатор пользователя.
            normalized_query: Нормализованный запрос пользователя.
            limit: Максимальное число рекомендаций.

        Returns:
            list[RecommendationResult]: Отсортированные рекомендации без избранного.
        """
        favorites = await self._load_favorites(user_id)
        queries, mode, _error = await self._hf_llm_client.build_search_queries_with_meta(
            description=normalized_query,
            genre_hint=None,
        )
        search_plan = build_search_plan(
            normalized_query=normalized_query,
            generated_queries=queries,
        )
        if not search_plan:
            return []

        excluded_ids = {int(item.anime_id) for item in favorites}
        taste_genres = Counter(genre for favorite in favorites for genre in (favorite.genres or []))
        query_terms = extract_terms(normalized_query)
        subject_terms = extract_subject_terms(normalized_query)
        scored: dict[int, tuple[CandidateScore, RecommendationResult]] = {}

        for index, plan in enumerate(search_plan):
            search_query = str(plan["query"]).strip()
            candidates = await self._search_candidates(search_query, limit)
            variant_terms = extract_terms(search_query)
            for anime in candidates:
                anime_id = int(anime.external_id or 0)
                if anime_id <= 0 or anime_id in excluded_ids:
                    continue
                score = score_candidate(
                    anime,
                    plan_index=index,
                    query_terms=query_terms,
                    variant_terms=variant_terms,
                    subject_terms=subject_terms,
                    taste_genres=taste_genres,
                )
                current = scored.get(anime_id)
                if current is not None and current[0].score >= score.score:
                    continue
                scored[anime_id] = (
                    score,
                    build_recommendation(
                        anime,
                        score,
                        prompt=normalized_query,
                        mode=mode,
                        query_source=str(plan["source"]).strip(),
                    ),
                )
        return finalize_recommendations(
            list(scored.values()),
            has_explicit_subject=bool(subject_terms),
            subject_terms=subject_terms,
            limit=limit,
        )

    async def _load_favorites(self, user_id: int) -> list[Favorite]:
        """Прочитать избранное пользователя отдельной транзакцией.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            list[Favorite]: Избранные тайтлы пользователя.
        """
        async with self._unit_of_work as uow:
            repository = uow.repository(FavoriteRepository)
            return await repository.get_by_user(user_id)

    async def _search_candidates(self, search_query: str, limit: int) -> list[Anime]:
        """Найти тайтлы по описанию, при пустом ответе — по названию.

        Args:
            search_query: Вариант поиска.
            limit: Максимальное число рекомендаций.

        Returns:
            list[Anime]: Карточки тайтлов из каталога.
        """
        page_limit = search_limit_for(limit)
        candidates = await self._anime_api_client.search_by_description(
            description=search_query,
            limit=page_limit,
        )
        if candidates:
            return candidates
        return await self._anime_api_client.search_by_title(
            title=search_query,
            limit=page_limit,
        )
