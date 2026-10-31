"""Правила подбора рекомендаций: оценка похожести тайтлов и сборка выдачи.

Здесь живёт знание о том, что считать «похожим аниме»: веса релевантности,
порядок планов поиска и формулировка пояснения. Словарь (стоп-слова, термы,
окончания) отделён в :mod:`recommendation_lexicon`, а сценарии только
оркестрируют обращения к каталогу и модели.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence

from backend.domain.entities.anime.anime import Anime
from backend.domain.policies.recommendation_lexicon import (
    anime_text,
    extract_terms,
    title_and_description,
)
from backend.domain.value_objects.recommendation.candidate_score import CandidateScore
from backend.domain.value_objects.recommendation.recommendation_result import (
    RecommendationResult,
)

LLM_TEXT_MODES = frozenset({"hf_llm_text", "gemini_llm_text"})
SCORE_ROUND_DIGITS = 3
RATING_SCORE_DIVISOR = 25
BASE_PLAN_WEIGHT = 1.35
PLAN_WEIGHT_STEP = 0.12
MIN_PLAN_WEIGHT = 0.25
VARIANT_RELEVANCE_WEIGHT = 1.55
QUERY_RELEVANCE_WEIGHT = 0.7
SUBJECT_HITS_WEIGHT = 1.4
GENRE_OVERLAP_WEIGHT = 0.14
SEARCH_LIMIT_MULTIPLIER = 2
MIN_SEARCH_LIMIT = 8
DESCRIPTION_PREVIEW = "Описание недоступно"
GENRE_REASON_LIMIT = 3
TITLE_PREVIEW_TEMPLATE = "Anime #{anime_id}"
WATCH_URL_TEMPLATE = "/watch/{anime_id}?episode=1"
USER_QUERY_SOURCE = "user_query"
AI_QUERY_SOURCE = "ai_query"

TASTE_KEYWORD_MIN_LENGTH = 3
GENRE_TASTE_WEIGHT = 0.6
KEYWORD_TASTE_WEIGHT = 0.3
RATING_TASTE_WEIGHT = 0.1
RATING_SCALE = 10.0


def score_term_overlap(query_terms: Sequence[str], anime: Anime) -> float:
    """Оценить долю термов запроса, совпавших с карточкой аниме.

    Args:
        query_terms: Значимые термы запроса.
        anime: Карточка тайтла из каталога.

    Returns:
        float: Доля совпавших термов либо 0.0 при отсутствии совпадений.
    """
    if not query_terms:
        return 0.0
    anime_terms = set(extract_terms(anime_text(anime)))
    if not anime_terms:
        return 0.0
    matches = sum(1 for term in query_terms if term in anime_terms)
    if matches <= 0:
        return 0.0
    return matches / max(len(query_terms), 1)


def score_subject_overlap(subject_terms: Sequence[str], anime: Anime) -> int:
    """Оценить совпадение предмета запроса с карточкой аниме.

    Args:
        subject_terms: Термы явной темы запроса.
        anime: Карточка тайтла из каталога.

    Returns:
        int: Число совпавших термов темы.
    """
    if not subject_terms:
        return 0
    anime_terms = set(extract_terms(anime_text(anime)))
    return sum(1 for term in subject_terms if term in anime_terms)


def build_search_plan(
    normalized_query: str,
    generated_queries: Sequence[str],
) -> list[dict[str, str]]:
    """Построить план поиска по запросу и вариантам модели.

    Args:
        normalized_query: Нормализованный запрос пользователя.
        generated_queries: Варианты поиска, предложенные моделью.

    Returns:
        list[dict[str, str]]: Уникальные варианты поиска с указанием источника.
    """
    unique: list[dict[str, str]] = []
    seen: set[str] = set()
    for query, source in [
        (normalized_query, USER_QUERY_SOURCE),
        *[(item, AI_QUERY_SOURCE) for item in generated_queries],
    ]:
        sanitized = str(query or "").strip()
        key = sanitized.lower()
        if not sanitized or key in seen:
            continue
        seen.add(key)
        unique.append({"query": sanitized, "source": source})
    return unique


def search_limit_for(limit: int) -> int:
    """Рассчитать размер выборки из каталога для выдачи нужного числа тайтлов.

    Args:
        limit: Максимальное число рекомендаций в выдаче.

    Returns:
        int: Число карточек, которые стоит запросить у каталога.
    """
    return max(int(limit) * SEARCH_LIMIT_MULTIPLIER, MIN_SEARCH_LIMIT)


def score_candidate(
    anime: Anime,
    *,
    plan_index: int,
    query_terms: Sequence[str],
    variant_terms: Sequence[str],
    subject_terms: Sequence[str],
    taste_genres: Iterable[str],
) -> CandidateScore:
    """Оценить кандидата по одному варианту поиска.

    Вес плана убывает с порядком: вариант пользователя важнее расширений модели.
    Профиль вкуса влияет только через пересечение жанров и не может перевесить
    смысл запроса.

    Args:
        anime: Карточка тайтла из каталога.
        plan_index: Порядковый номер варианта поиска в плане.
        query_terms: Значимые термы исходного запроса.
        variant_terms: Значимые термы текущего варианта поиска.
        subject_terms: Термы явной темы запроса.
        taste_genres: Жанры из избранного пользователя.

    Returns:
        CandidateScore: Балл релевантности и его составляющие.
    """
    genre_overlap = len(set(anime.genres or []) & set(taste_genres))
    query_relevance = score_term_overlap(query_terms=query_terms, anime=anime)
    variant_relevance = score_term_overlap(query_terms=variant_terms, anime=anime)
    subject_hits = score_subject_overlap(subject_terms=subject_terms, anime=anime)
    topical_relevance = max(query_relevance, variant_relevance, float(subject_hits))
    score = (
        max(MIN_PLAN_WEIGHT, BASE_PLAN_WEIGHT - plan_index * PLAN_WEIGHT_STEP)
        + variant_relevance * VARIANT_RELEVANCE_WEIGHT
        + query_relevance * QUERY_RELEVANCE_WEIGHT
        + subject_hits * SUBJECT_HITS_WEIGHT
        + genre_overlap * GENRE_OVERLAP_WEIGHT
        + float(anime.rating or 0) / RATING_SCORE_DIVISOR
    )
    return CandidateScore(
        score=score,
        subject_hits=subject_hits,
        topical_relevance=topical_relevance,
        genre_overlap=genre_overlap,
    )


def build_reason(
    prompt: str,
    anime_title: str,
    genres: Sequence[str],
    mode: str,
    query_source: str,
    subject_hits: int,
    genre_overlap: int,
) -> str:
    """Собрать пояснение, почему тайтл попал в рекомендации.

    Args:
        prompt: Нормализованный запрос пользователя.
        anime_title: Название тайтла.
        genres: Жанры тайтла.
        mode: Способ разбора запроса моделью.
        query_source: Источник варианта поиска.
        subject_hits: Число совпадений явной темы запроса.
        genre_overlap: Число совпавших жанров с избранным пользователя.

    Returns:
        str: Текст пояснения для карточки рекомендации.
    """
    genre_part = f" Жанровый профиль: {', '.join(genres[:GENRE_REASON_LIMIT])}." if genres else ""
    mode_part = " Запрос разобран через AI." if mode in LLM_TEXT_MODES else ""
    source_part = (
        " Сначала учтен прямой запрос пользователя."
        if query_source == USER_QUERY_SOURCE
        else " AI расширил исходный запрос дополнительным вариантом поиска."
    )
    subject_part = " Явная тема запроса совпала с содержанием тайтла." if subject_hits > 0 else ""
    profile_part = (
        " Профиль пользователя использован только как мягкий бонус при сортировке."
        if genre_overlap > 0
        else ""
    )
    return (
        f"Подборка под запрос «{prompt}». {anime_title} подобран по смыслу запроса."
        f"{source_part}{subject_part}{profile_part}{genre_part}{mode_part}"
    ).strip()


def build_recommendation(
    anime: Anime,
    score: CandidateScore,
    *,
    prompt: str,
    mode: str,
    query_source: str,
) -> RecommendationResult:
    """Собрать карточку рекомендации из оценённого кандидата.

    Args:
        anime: Карточка тайтла из каталога.
        score: Балл релевантности кандидата.
        prompt: Нормализованный запрос пользователя.
        mode: Способ разбора запроса моделью.
        query_source: Источник варианта поиска, нашедшего тайтл.

    Returns:
        RecommendationResult: Готовая рекомендация для выдачи.
    """
    anime_id = int(anime.external_id or 0)
    title = anime.title or TITLE_PREVIEW_TEMPLATE.format(anime_id=anime_id)
    return RecommendationResult(
        anime_id=anime_id,
        reason=build_reason(
            prompt=prompt,
            anime_title=title,
            genres=anime.genres or [],
            mode=mode,
            query_source=query_source,
            subject_hits=score.subject_hits,
            genre_overlap=score.genre_overlap,
        ),
        similarity_score=round(score.score, SCORE_ROUND_DIGITS),
        title=title,
        description=anime.description or DESCRIPTION_PREVIEW,
        image_url=anime.cover_url,
        genres=anime.genres or [],
        watch_url=WATCH_URL_TEMPLATE.format(anime_id=anime_id),
    )


def finalize_recommendations(
    candidates: Sequence[tuple[CandidateScore, RecommendationResult]],
    *,
    has_explicit_subject: bool,
    subject_terms: Sequence[str],
    limit: int,
) -> list[RecommendationResult]:
    """Отфильтровать и отсортировать кандидатов перед выдачей.

    Args:
        candidates: Пары «оценка, рекомендация» по идентификаторам тайтлов.
        has_explicit_subject: Был ли в запросе явно указанный предмет.
        subject_terms: Термы явной темы запроса.
        limit: Максимальное число рекомендаций.

    Returns:
        list[RecommendationResult]: Рекомендации в порядке убывания балла.
    """
    filtered = list(candidates)
    if has_explicit_subject and any(score.topical_relevance > 0 for score, _ in filtered):
        filtered = [pair for pair in filtered if pair[0].topical_relevance > 0]
    if subject_terms and any(score.subject_hits > 0 for score, _ in filtered):
        filtered = [pair for pair in filtered if pair[0].subject_hits > 0]
    recommendations = [recommendation for _score, recommendation in filtered]
    recommendations.sort(key=lambda item: item.similarity_score, reverse=True)
    return recommendations[: max(int(limit), 1)]


def taste_keywords(description: str) -> list[str]:
    """Разобрать описание хайлайта на слова-маркеры вкуса.

    Args:
        description: Описание хайлайта, оставленного пользователем.

    Returns:
        list[str]: Слова длиннее служебного порога в нижнем регистре.
    """
    return [
        word
        for word in str(description or "").lower().split()
        if len(word) > TASTE_KEYWORD_MIN_LENGTH
    ]


def score_taste_similarity(
    anime: Anime,
    *,
    taste_genres: Iterable[str],
    keyword_weights: Counter[str],
) -> float:
    """Оценить близость тайтла к вкусу пользователя по жанрам и словам.

    Args:
        anime: Карточка тайтла из каталога.
        taste_genres: Жанры избранного пользователя.
        keyword_weights: Частоты слов из описаний хайлайтов пользователя.

    Returns:
        float: Вес похожести; ноль, если сходства нет.
    """
    genre_overlap = len(set(anime.genres or []) & set(taste_genres))
    searchable_text = title_and_description(anime)
    keyword_overlap = sum(
        weight
        for keyword, weight in keyword_weights.items()
        if len(keyword) > TASTE_KEYWORD_MIN_LENGTH and keyword in searchable_text
    )
    rating_weight = float(anime.rating or 0) / RATING_SCALE
    return (
        genre_overlap * GENRE_TASTE_WEIGHT
        + keyword_overlap * KEYWORD_TASTE_WEIGHT
        + rating_weight * RATING_TASTE_WEIGHT
    )
