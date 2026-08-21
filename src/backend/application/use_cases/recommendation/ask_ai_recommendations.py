from __future__ import annotations

import re
from collections import Counter

from starlette import status

from backend.application.dto import AskAiRecommendationsCommand
from backend.application.interface.repositories.favorite_repository import FavoriteRepository
from backend.application.interface.services import AnimeApiClientInterface as AnimeApiClient
from backend.application.interface.services import LLMClientInterface as HuggingFaceLLMClient
from backend.application.use_cases.recommendation.result import RecommendationUseCaseResult
from backend.domain import RecommendationResult


class AskAiRecommendationsUseCase:
    """Подбирает рекомендации по свободному текстовому запросу пользователя."""

    _STOP_WORDS = {
        "a",
        "about",
        "all",
        "an",
        "and",
        "anime",
        "anim",
        "as",
        "at",
        "be",
        "but",
        "for",
        "from",
        "good",
        "hero",
        "i",
        "if",
        "in",
        "is",
        "it",
        "like",
        "more",
        "my",
        "no",
        "not",
        "of",
        "on",
        "or",
        "show",
        "similar",
        "something",
        "than",
        "that",
        "the",
        "this",
        "to",
        "want",
        "with",
        "без",
        "более",
        "бы",
        "в",
        "во",
        "вроде",
        "где",
        "для",
        "или",
        "как",
        "какое",
        "какой",
        "какую",
        "ли",
        "мне",
        "на",
        "не",
        "но",
        "ну",
        "о",
        "об",
        "под",
        "по",
        "пожалуйста",
        "посоветуй",
        "посоветуйте",
        "про",
        "с",
        "со",
        "только",
        "у",
        "хочу",
        "что",
        "что-то",
        "чтобы",
        "это",
        "этот",
        "эту",
        "аним",
    }
    _SUBJECT_PATTERNS = (
        re.compile(r"(?:^|\s)(?:про|about)\s+([^,.!?]+)", re.IGNORECASE),
        re.compile(r"(?:^|\s)(?:with|с)\s+([^,.!?]+)", re.IGNORECASE),
    )

    def __init__(
        self,
        favorite_repo: FavoriteRepository,
        anime_api_client: AnimeApiClient,
        hf_llm_client: HuggingFaceLLMClient,
    ):
        self.favorite_repo = favorite_repo
        self.anime_api_client = anime_api_client
        self.hf_llm_client = hf_llm_client

    async def execute(
        self,
        command: AskAiRecommendationsCommand,
    ) -> RecommendationUseCaseResult:
        normalized_query = str(command.query or "").strip()
        if not normalized_query:
            return await RecommendationUseCaseResult.failure(
                "invalid_query",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return await RecommendationUseCaseResult.success(
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
        limit: int = 6,
    ) -> list[RecommendationResult]:
        favorites = await self.favorite_repo.get_by_user(user_id)
        queries, mode, _error = await self.hf_llm_client.build_search_queries_with_meta(
            description=normalized_query,
            genre_hint=None,
        )
        existing_ids = {int(item.anime_id) for item in favorites}
        top_genres = Counter(genre for favorite in favorites for genre in (favorite.genres or []))
        search_plan = await self._build_search_plan(
            normalized_query=normalized_query,
            generated_queries=queries,
        )
        if not search_plan:
            return []

        query_terms = await self._extract_terms(normalized_query)
        subject_terms = await self._extract_subject_terms(normalized_query)
        has_explicit_subject = bool(subject_terms)
        scored_candidates: dict[int, dict[str, object]] = {}

        for index, plan in enumerate(search_plan):
            search_query = str(plan["query"]).strip()
            query_source = str(plan["source"]).strip()
            candidates = await self.anime_api_client.search_by_description(
                description=search_query,
                limit=max(limit * 2, 8),
            )
            if not candidates:
                candidates = await self.anime_api_client.search_by_title(
                    title=search_query,
                    limit=max(limit * 2, 8),
                )
            query_variant_terms = await self._extract_terms(search_query)
            for anime in candidates:
                anime_id = int(anime.external_id or 0)
                if anime_id <= 0 or anime_id in existing_ids:
                    continue
                genre_overlap = len(set(anime.genres or []) & set(top_genres.keys()))
                query_relevance = await self._score_term_overlap(
                    query_terms=query_terms,
                    anime=anime,
                )
                variant_relevance = await self._score_term_overlap(
                    query_terms=query_variant_terms,
                    anime=anime,
                )
                subject_hits = await self._score_subject_overlap(
                    subject_terms=subject_terms,
                    anime=anime,
                )
                topical_relevance = max(
                    query_relevance,
                    variant_relevance,
                    float(subject_hits),
                )
                score = (
                    max(0.25, 1.35 - index * 0.12)
                    + variant_relevance * 1.55
                    + query_relevance * 0.7
                    + subject_hits * 1.4
                    + genre_overlap * 0.14
                    + float(anime.rating or 0) / 25
                )
                current = scored_candidates.get(anime_id)
                if current and float(current["score"]) >= score:
                    continue
                scored_candidates[anime_id] = {
                    "score": score,
                    "subject_hits": subject_hits,
                    "topical_relevance": topical_relevance,
                    "query_source": query_source,
                    "recommendation": RecommendationResult(
                        anime_id=anime_id,
                        reason=await self._build_reason(
                            prompt=normalized_query,
                            anime_title=anime.title or f"Anime #{anime_id}",
                            genres=anime.genres or [],
                            mode=mode,
                            query_source=query_source,
                            subject_hits=subject_hits,
                            genre_overlap=genre_overlap,
                        ),
                        similarity_score=round(score, 3),
                        title=anime.title or f"Anime #{anime_id}",
                        description=anime.description or "Описание недоступно",
                        image_url=anime.cover_url,
                        genres=anime.genres or [],
                        watch_url=f"/watch/{anime_id}?episode=1",
                    ),
                }
        filtered_candidates = list(scored_candidates.values())
        if has_explicit_subject and any(
            float(item["topical_relevance"]) > 0 for item in filtered_candidates
        ):
            filtered_candidates = [
                item for item in filtered_candidates if float(item["topical_relevance"]) > 0
            ]
        if subject_terms and any(int(item["subject_hits"]) > 0 for item in filtered_candidates):
            filtered_candidates = [
                item for item in filtered_candidates if int(item["subject_hits"]) > 0
            ]
        recommendations = [item["recommendation"] for item in filtered_candidates]
        for recommendation in recommendations:
            recommendation.similarity_score = round(float(recommendation.similarity_score), 3)
        recommendations.sort(key=lambda item: item.similarity_score, reverse=True)
        return recommendations[: max(int(limit), 1)]

    async def _build_search_plan(
        self,
        normalized_query: str,
        generated_queries: list[str],
    ) -> list[dict[str, str]]:
        unique: list[dict[str, str]] = []
        seen: set[str] = set()
        for query, source in [
            (normalized_query, "user_query"),
            *[(item, "ai_query") for item in generated_queries],
        ]:
            sanitized = str(query or "").strip()
            key = sanitized.lower()
            if not sanitized or key in seen:
                continue
            seen.add(key)
            unique.append({"query": sanitized, "source": source})
        return unique

    async def _extract_terms(self, value: str) -> list[str]:
        normalized_terms: list[str] = []
        seen: set[str] = set()
        for raw_term in re.findall(r"[a-zA-Zа-яА-Я0-9-]+", str(value or "").lower()):
            term = await self._normalize_term(raw_term)
            if len(term) < 3 or term in self._STOP_WORDS or term in seen:
                continue
            seen.add(term)
            normalized_terms.append(term)
        return normalized_terms

    async def _extract_subject_terms(self, query: str) -> list[str]:
        subject_terms: list[str] = []
        for pattern in self._SUBJECT_PATTERNS:
            match = pattern.search(str(query or ""))
            if not match:
                continue
            subject_terms.extend(await self._extract_terms(match.group(1)))
        return subject_terms

    async def _normalize_term(self, value: str) -> str:
        term = str(value or "").strip().lower()
        for suffix in (
            "ами",
            "ями",
            "ого",
            "ему",
            "ому",
            "ыми",
            "ими",
            "ах",
            "ях",
            "ов",
            "ев",
            "ей",
            "ам",
            "ям",
            "ом",
            "ем",
            "ой",
            "ий",
            "ый",
            "ая",
            "ое",
            "ые",
            "ть",
            "ти",
            "ing",
            "ers",
            "ies",
            "es",
            "ed",
            "er",
            "ly",
            "s",
            "а",
            "я",
            "ы",
            "и",
            "е",
            "у",
            "ю",
            "о",
        ):
            if len(term) > len(suffix) + 2 and term.endswith(suffix):
                return term[: -len(suffix)]
        return term

    async def _score_term_overlap(self, query_terms: list[str], anime) -> float:
        if not query_terms:
            return 0.0
        anime_terms = set(
            await self._extract_terms(
                " ".join(
                    [
                        str(anime.title or ""),
                        str(anime.description or ""),
                        " ".join(anime.genres or []),
                    ]
                )
            )
        )
        if not anime_terms:
            return 0.0
        matches = sum(1 for term in query_terms if term in anime_terms)
        if matches <= 0:
            return 0.0
        return matches / max(len(query_terms), 1)

    async def _score_subject_overlap(self, subject_terms: list[str], anime) -> int:
        if not subject_terms:
            return 0
        anime_terms = set(
            await self._extract_terms(
                " ".join(
                    [
                        str(anime.title or ""),
                        str(anime.description or ""),
                        " ".join(anime.genres or []),
                    ]
                )
            )
        )
        return sum(1 for term in subject_terms if term in anime_terms)

    async def _build_reason(
        self,
        prompt: str,
        anime_title: str,
        genres: list[str],
        mode: str,
        query_source: str,
        subject_hits: int,
        genre_overlap: int,
    ) -> str:
        genre_part = f" Жанровый профиль: {', '.join(genres[:3])}." if genres else ""
        mode_part = (
            " Запрос разобран через AI." if mode in {"hf_llm_text", "gemini_llm_text"} else ""
        )
        source_part = (
            " Сначала учтен прямой запрос пользователя."
            if query_source == "user_query"
            else " AI расширил исходный запрос дополнительным вариантом поиска."
        )
        subject_part = (
            " Явная тема запроса совпала с содержанием тайтла." if subject_hits > 0 else ""
        )
        profile_part = (
            " Профиль пользователя использован только как мягкий бонус при сортировке."
            if genre_overlap > 0
            else ""
        )
        return (
            f"Подборка под запрос «{prompt}». {anime_title} подобран по смыслу запроса."
            f"{source_part}{subject_part}{profile_part}{genre_part}{mode_part}"
        ).strip()
