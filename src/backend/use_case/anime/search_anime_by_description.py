import re
from typing import List
from src.backend.domain.anime.entity import Anime
from src.backend.domain.anime.policy import AnimeSafetyPolicy
from src.backend.domain.anime.value_object import SearchAnimeByDescriptionResult
from src.backend.infrastructure.external.anime_api_client import AnimeApiClient
from src.backend.infrastructure.external.huggingface_llm_client import HuggingFaceLLMClient


class SearchAnimeByDescriptionUseCase:
    """
    Поиск аниме по описанию через AniList GraphQL
    """

    def __init__(
        self,
        api_client: AnimeApiClient,
        llm_client: HuggingFaceLLMClient,
        safety_policy: AnimeSafetyPolicy | None = None
    ):
        self.api_client = api_client
        self.llm_client = llm_client
        self.safety_policy = safety_policy or AnimeSafetyPolicy()

    def execute(
        self,
        description: str,
        genre_hint: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        min_rating: int | None = None,
        age_rating: str = "all",
        adult_confirmed: bool = False,
        sort_by: str = "match",
        limit: int = 10
    ) -> SearchAnimeByDescriptionResult:
        """
        Возвращает список объектов Anime, найденных по описанию
        """
        base_description = description.strip()
        if not base_description:
            return SearchAnimeByDescriptionResult(items=[])

        explicit_adult_intent = self.safety_policy.has_explicit_adult_intent(base_description, genre_hint)
        if explicit_adult_intent and not adult_confirmed:
            return SearchAnimeByDescriptionResult(
                items=[],
                requires_age_confirmation=True,
                message="Найден запрос с 18+ контентом. Подтвердите, что вам есть 18 лет.",
            )
        include_adult = adult_confirmed and (age_rating == "18+" or explicit_adult_intent)

        llm_queries, llm_mode, llm_error = self.llm_client.build_search_queries_with_meta(
            description=base_description,
            genre_hint=genre_hint,
            year_from=year_from,
            year_to=year_to,
            min_rating=min_rating,
            allow_adult=include_adult
        )
        query_preview = " | ".join(llm_queries[:3])
        if llm_error:
            print(f"[AI_SEARCH] mode={llm_mode} queries='{query_preview}' error='{llm_error}'")
        else:
            print(f"[AI_SEARCH] mode={llm_mode} queries='{query_preview}'")

        queries = self._build_queries(llm_queries, base_description)
        title_queries = self._build_title_queries(base_description, llm_queries, genre_hint)
        expanded_limit = max(limit * 2, limit)

        results: List[Anime] = []
        for candidate in title_queries:
            batch = self.api_client.search_by_title(
                title=candidate,
                include_adult=include_adult,
                limit=expanded_limit
            )
            results = self._merge_unique(results, batch)

        for candidate in queries:
            batch = self.api_client.search_by_description(
                description=candidate,
                year_from=year_from,
                year_to=year_to,
                min_rating=min_rating,
                include_adult=include_adult,
                limit=expanded_limit
            )
            results = self._merge_unique(results, batch)

        if not results:
            for candidate in queries:
                batch = self.api_client.search_by_description(
                    description=candidate,
                    include_adult=include_adult,
                    limit=expanded_limit
                )
                results = self._merge_unique(results, batch)

        if not include_adult:
            results = [item for item in results if not self.safety_policy.is_probably_nsfw(item)]

        ordered = self._sort_results(
            items=results,
            sort_by=sort_by,
            description=base_description,
            genre_hint=genre_hint
        )
        return SearchAnimeByDescriptionResult(items=ordered[:limit])

    def _build_queries(self, optimized_queries: List[str], raw_description: str) -> List[str]:
        """Собирает список уникальных запросов: исходный текст пользователя + LLM-варианты."""
        variants: List[str] = []
        seen: set[str] = set()
        candidates = [raw_description, *optimized_queries]
        for value in candidates:
            normalized = self._normalize(value)
            if normalized and normalized not in seen:
                seen.add(normalized)
                variants.append(value.strip())
        return variants

    def _build_title_queries(
        self,
        raw_description: str,
        optimized_queries: List[str],
        genre_hint: str | None
    ) -> List[str]:
        """Собирает кандидаты названий для прямого title-поиска."""
        variants: List[str] = []
        seen: set[str] = set()

        for hint in self.safety_policy.suggest_title_hints(raw_description, genre_hint):
            normalized = self._normalize(hint)
            if normalized and normalized not in seen:
                seen.add(normalized)
                variants.append(hint.strip())

        for candidate in optimized_queries:
            normalized = self._normalize(candidate)
            words_count = len(candidate.split())
            if not normalized or normalized in seen:
                continue
            if words_count > 7:
                continue
            seen.add(normalized)
            variants.append(candidate.strip())

        return variants

    def _merge_unique(self, base: List[Anime], incoming: List[Anime]) -> List[Anime]:
        """Объединяет списки аниме без дубликатов."""
        merged = list(base)
        seen = {
            (item.external_id or "").strip().lower() or (item.title or "").strip().lower()
            for item in merged
        }
        for item in incoming:
            key = (item.external_id or "").strip().lower() or (item.title or "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(item)
        return merged

    def _sort_results(
        self,
        items: List[Anime],
        sort_by: str,
        description: str,
        genre_hint: str | None
    ) -> List[Anime]:
        """Сортирует выдачу по рейтингу, году или релевантности."""
        if sort_by == "rating":
            return sorted(items, key=lambda x: x.rating or 0, reverse=True)
        if sort_by == "year":
            return sorted(items, key=lambda x: x.year or 0, reverse=True)
        query_tokens = self._tokenize(f"{description} {genre_hint or ''}")
        return sorted(items, key=lambda x: self._match_score(x, query_tokens), reverse=True)

    def _match_score(self, anime: Anime, query_tokens: List[str]) -> float:
        """Считает простой score релевантности по вхождению токенов в title/description."""
        if not query_tokens:
            return anime.rating or 0
        title = self._normalize(anime.title or "")
        genres = " ".join(anime.genres or [])
        synopsis = re.sub(r"<[^>]+>", " ", anime.description or "")
        haystack = self._normalize(f"{anime.title or ''} {genres} {synopsis}")

        score = 0.0
        for token in query_tokens:
            if token in title:
                score += 3.0
            elif token in haystack:
                score += 1.0
        return score + float(anime.rating or 0) * 0.1

    def _tokenize(self, value: str) -> List[str]:
        """Извлекает поисковые токены из русского/английского текста."""
        tokens = re.findall(r"[a-zA-Zа-яА-Я0-9]{3,}", value.lower())
        seen: set[str] = set()
        result: List[str] = []
        for token in tokens:
            if token in seen:
                continue
            seen.add(token)
            result.append(token)
        return result

    def _normalize(self, value: str) -> str:
        return " ".join((value or "").lower().split())
