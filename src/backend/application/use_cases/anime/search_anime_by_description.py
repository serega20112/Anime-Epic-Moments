"""Сценарий поиска аниме по описанию на естественном языке."""

from __future__ import annotations

import logging
import re

from backend.application.dto.anime import SearchAnimeByDescriptionQuery
from backend.application.interface.services import AnimeApiClientInterface, LLMClientInterface
from backend.domain.entities.anime.anime import Anime
from backend.domain.policies.anime_safety_policy import AnimeSafetyPolicy
from backend.domain.value_objects.anime.search_result import SearchAnimeByDescriptionResult

logger = logging.getLogger("anime_epic_moments")

MAX_TITLE_QUERY_WORDS = 7
QUERY_PREVIEW_LIMIT = 3
TITLE_MATCH_BONUS = 20.0
TITLE_CONTAINS_BONUS = 10.0
TOKEN_TITLE_BONUS = 3.0
TOKEN_TEXT_BONUS = 1.0
RATING_WEIGHT = 0.1
ADULT_RATING = "18+"
ADULT_INTENT_MESSAGE = (
    "Запрос выглядит как 18+ контент, но выбран возрастной рейтинг ниже 18+. "
    "Поставьте 18+ чтобы искать такой контент."
)
AGE_CONFIRMATION_MESSAGE = "Найден запрос с 18+ контентом. Подтвердите, что вам есть 18 лет."


def normalize_text(value: str) -> str:
    """Свернуть регистр и повторяющиеся пробелы в тексте.

    Args:
        value: Исходный текст.

    Returns:
        str: Текст в нижнем регистре с одинарными пробелами.
    """
    return " ".join((value or "").lower().split())


def tokenize(value: str) -> list[str]:
    """Извлечь поисковые токены из русского или английского текста.

    Args:
        value: Текст описания и подсказки жанра.

    Returns:
        list[str]: Уникальные токены длиннее двух символов в порядке появления.
    """
    seen: set[str] = set()
    result: list[str] = []
    for token in re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9]{3,}", value.lower()):
        if token in seen:
            continue
        seen.add(token)
        result.append(token)
    return result


class SearchAnimeByDescriptionUseCase:
    """Ищет аниме по описанию через LLM-варианты запросов и клиент каталога."""

    def __init__(
        self,
        api_client: AnimeApiClientInterface,
        llm_client: LLMClientInterface,
        safety_policy: AnimeSafetyPolicy,
    ) -> None:
        """Собрать сценарий поиска по описанию.

        Args:
            api_client: Клиент API аниме.
            llm_client: Клиент LLM для построения вариантов запроса.
            safety_policy: Политика возрастной безопасности каталога.
        """
        self._api_client = api_client
        self._llm_client = llm_client
        self._safety_policy = safety_policy

    async def execute(self, query: SearchAnimeByDescriptionQuery) -> SearchAnimeByDescriptionResult:
        """Найти аниме, подходящее описанию на естественном языке.

        Args:
            query: Описание, фильтры и подтверждение возраста пользователя.

        Returns:
            SearchAnimeByDescriptionResult: Найденные тайтлы либо просьба
                подтвердить возраст.
        """
        description = query.description.strip()
        if not description:
            return SearchAnimeByDescriptionResult(items=[])

        adult_gate = self._adult_gate(description, query)
        if adult_gate is not None:
            return adult_gate
        include_adult = bool(query.adult_confirmed) and query.age_rating == ADULT_RATING

        llm_queries, llm_mode, llm_error = await self._llm_client.build_search_queries_with_meta(
            description=description,
            genre_hint=query.genre_hint,
            year_from=query.year_from,
            year_to=query.year_to,
            min_rating=query.min_rating,
            age_rating=query.age_rating,
            allow_adult=include_adult,
        )
        query_preview = " | ".join(llm_queries[:QUERY_PREVIEW_LIMIT])
        if llm_error:
            logger.warning(
                "ai_search_failed mode=%s queries=%s error=%s",
                llm_mode,
                query_preview,
                llm_error,
            )
        else:
            logger.info("ai_search mode=%s queries=%s", llm_mode, query_preview)

        queries = self._build_queries(llm_queries, description)
        title_queries = self._build_title_queries(description, llm_queries, query.genre_hint)
        expanded_limit = max(query.limit * 2, query.limit)

        results = await self._collect_results(
            title_queries, queries, query, include_adult, expanded_limit
        )
        if not include_adult:
            results = [item for item in results if not self._safety_policy.is_probably_nsfw(item)]

        ordered = self._sort_results(
            items=results,
            sort_by=query.sort_by,
            description=description,
            genre_hint=query.genre_hint,
            llm_title_hints=title_queries,
        )
        return SearchAnimeByDescriptionResult(items=ordered[: query.limit])

    def _adult_gate(
        self,
        description: str,
        query: SearchAnimeByDescriptionQuery,
    ) -> SearchAnimeByDescriptionResult | None:
        """Проверить 18+ намерение запроса до обращения к внешним сервисам.

        Args:
            description: Описание пользователя без пробелов по краям.
            query: Исходный запрос поиска с возрастными флагами.

        Returns:
            SearchAnimeByDescriptionResult | None: Ответ-отказ либо None,
            если запрос можно обрабатывать.
        """
        if not self._safety_policy.has_explicit_adult_intent(description, query.genre_hint):
            return None
        if query.age_rating != ADULT_RATING:
            return SearchAnimeByDescriptionResult(
                items=[], requires_age_confirmation=False, message=ADULT_INTENT_MESSAGE
            )
        if not query.adult_confirmed:
            return SearchAnimeByDescriptionResult(
                items=[], requires_age_confirmation=True, message=AGE_CONFIRMATION_MESSAGE
            )
        return None

    async def _collect_results(
        self,
        title_queries: list[str],
        queries: list[str],
        query: SearchAnimeByDescriptionQuery,
        include_adult: bool,
        expanded_limit: int,
    ) -> list[Anime]:
        """Собрать уникальные тайтлы из поиска по названию и по описанию.

        При пустой выдаче с фильтрами года и рейтинга запрос повторяется без
        них: так редкий тайтл не теряется из-за слишком узких ограничений.

        Args:
            title_queries: Кандидаты названий для прямого поиска.
            queries: Варианты описательных запросов.
            query: Исходный запрос с фильтрами года и рейтинга.
            include_adult: Искать ли 18+ контент.
            expanded_limit: Расширенный лимит выборки на один запрос.

        Returns:
            list[Anime]: Найденные тайтлы без повторов.
        """
        results: list[Anime] = []
        for candidate in title_queries:
            batch = await self._api_client.search_by_title(
                title=candidate,
                include_adult=include_adult,
                limit=expanded_limit,
            )
            results = self._merge_unique(results, batch)
        for candidate in queries:
            batch = await self._api_client.search_by_description(
                description=candidate,
                year_from=query.year_from,
                year_to=query.year_to,
                min_rating=query.min_rating,
                include_adult=include_adult,
                limit=expanded_limit,
            )
            results = self._merge_unique(results, batch)
        if results:
            return results
        for candidate in queries:
            batch = await self._api_client.search_by_description(
                description=candidate,
                include_adult=include_adult,
                limit=expanded_limit,
            )
            results = self._merge_unique(results, batch)
        return results

    def _build_queries(self, optimized_queries: list[str], raw_description: str) -> list[str]:
        """Собрать уникальные запросы: исходный текст и варианты LLM.

        Args:
            optimized_queries: Варианты запросов от LLM.
            raw_description: Исходное описание пользователя.

        Returns:
            list[str]: Уникальные варианты запросов в порядке приоритета.
        """
        return self._unique_values([raw_description, *optimized_queries])

    def _build_title_queries(
        self,
        raw_description: str,
        optimized_queries: list[str],
        genre_hint: str | None,
    ) -> list[str]:
        """Собрать кандидаты названий для прямого поиска по title.

        Args:
            raw_description: Исходное описание пользователя.
            optimized_queries: Варианты запросов от LLM.
            genre_hint: Подсказка жанра из интерфейса.

        Returns:
            list[str]: Кандидаты названий без дублей и слишком длинных фраз.
        """
        hints = list(self._safety_policy.suggest_title_hints(raw_description, genre_hint))
        short_candidates = [
            candidate
            for candidate in optimized_queries
            if len(candidate.split()) <= MAX_TITLE_QUERY_WORDS
        ]
        return self._unique_values([*hints, *short_candidates])

    @staticmethod
    def _unique_values(candidates: list[str]) -> list[str]:
        """Оставить первые вхождения значений после нормализации текста.

        Args:
            candidates: Исходные строки-кандидаты.

        Returns:
            list[str]: Уникальные строки без пробелов по краям.
        """
        variants: list[str] = []
        seen: set[str] = set()
        for value in candidates:
            normalized = normalize_text(value)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            variants.append(value.strip())
        return variants

    @staticmethod
    def _merge_unique(base: list[Anime], incoming: list[Anime]) -> list[Anime]:
        """Объединить списки аниме без повторов по внешнему идентификатору.

        Args:
            base: Уже собранные тайтлы.
            incoming: Очередная партия результатов провайдера.

        Returns:
            list[Anime]: Обновлённый список без дублей.
        """
        merged = list(base)
        seen = {SearchAnimeByDescriptionUseCase._identity(item) for item in merged}
        for item in incoming:
            identity = SearchAnimeByDescriptionUseCase._identity(item)
            if not identity or identity in seen:
                continue
            seen.add(identity)
            merged.append(item)
        return merged

    @staticmethod
    def _identity(anime: Anime) -> str:
        """Вернуть ключ тайтла для сведения дублей из разных источников.

        Args:
            anime: Найденный тайтл.

        Returns:
            str: Внешний идентификатор либо название в нижнем регистре.
        """
        external_id = (anime.external_id or "").strip().lower()
        return external_id or (anime.title or "").strip().lower()

    def _sort_results(
        self,
        items: list[Anime],
        sort_by: str,
        description: str,
        genre_hint: str | None,
        llm_title_hints: list[str],
    ) -> list[Anime]:
        """Отсортировать выдачу по рейтингу, году или релевантности описанию.

        Args:
            items: Найденные тайтлы.
            sort_by: Выбранный критерий сортировки.
            description: Описание пользователя.
            genre_hint: Подсказка жанра из интерфейса.
            llm_title_hints: Кандидаты названий для усиления релевантности.

        Returns:
            list[Anime]: Упорядоченные тайтлы.
        """
        if sort_by == "rating":
            return sorted(items, key=lambda item: item.rating or 0, reverse=True)
        if sort_by == "year":
            return sorted(items, key=lambda item: item.year or 0, reverse=True)
        query_tokens = tokenize(f"{description} {genre_hint or ''}")
        normalized_hints = [normalize_text(hint) for hint in llm_title_hints]
        keyed = [(self._match_score(item, query_tokens, normalized_hints), item) for item in items]
        keyed.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _score, item in keyed]

    @staticmethod
    def _match_score(
        anime: Anime,
        query_tokens: list[str],
        normalized_hints: list[str],
    ) -> float:
        """Посчитать релевантность тайтла описанию и LLM-подсказкам.

        Args:
            anime: Оцениваемый тайтл.
            query_tokens: Токены описания пользователя.
            normalized_hints: Нормализованные кандидаты названий.

        Returns:
            float: Итоговый вес сортировки.
        """
        base_rating = float(anime.rating or 0)
        if not query_tokens and not normalized_hints:
            return base_rating

        title = normalize_text(anime.title or "")
        genres = " ".join(anime.genres or [])
        synopsis = re.sub(r"<[^>]+>", " ", anime.description or "")
        haystack = normalize_text(f"{anime.title or ''} {genres} {synopsis}")

        score = 0.0
        for token in query_tokens:
            if token in title:
                score += TOKEN_TITLE_BONUS
            elif token in haystack:
                score += TOKEN_TEXT_BONUS

        for hint in normalized_hints:
            if not hint or not title:
                continue
            if title == hint:
                score += TITLE_MATCH_BONUS
            elif hint in title or title in hint:
                score += TITLE_CONTAINS_BONUS

        return score + base_rating * RATING_WEIGHT
