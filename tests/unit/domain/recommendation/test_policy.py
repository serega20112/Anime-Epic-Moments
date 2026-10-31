from __future__ import annotations

from collections import Counter

import pytest

from backend.domain.entities.anime.anime import Anime
from backend.domain.policies.recommendation_lexicon import (
    extract_subject_terms,
    extract_terms,
    normalize_term,
)
from backend.domain.policies.recommendation_policy import (
    build_recommendation,
    build_search_plan,
    finalize_recommendations,
    score_candidate,
    score_taste_similarity,
    search_limit_for,
    taste_keywords,
)
from backend.domain.value_objects.recommendation.candidate_score import CandidateScore

GENRE_ANIME = Anime(
    external_id="20",
    title="Chi no Sweet Home",
    description="A small kitten finds a new family",
    genres=["Slice of Life", "Comedy"],
    rating=8.2,
)
SPORT_ANIME = Anime(
    external_id="21",
    title="Slam Dunk",
    description="A basketball team fights for the top",
    genres=["Sports", "Comedy"],
    rating=9.0,
)
KITTEN_ANIME = Anime(
    external_id="22",
    title="Кошечка Мими",
    description="Маленький котик находит новую семью",
    genres=["Slice of Life", "Comedy"],
    rating=7.5,
)


@pytest.mark.unit
class TestRecommendationLexicon:
    """Юнит-тесты разбора поисковых терминов рекомендаций."""

    def test_normalize_term_drops_inflection(self):
        """Что тестируем: сброс окончания при нормализации термина.
        Что передаём: слово с узнаваемым русским окончанием.
        Что ожидаем: остаётся основа, которой сравнивают запрос и карточку.
        """
        assert normalize_term("котиками") == "котик"
        assert normalize_term("  КотиКИ ") == "котик"

    def test_extract_terms_skips_stop_words_and_duplicates(self):
        """Что тестируем: разбор текста на значимые термы.
        Что передаём: фразу со стоп-словами и повторами.
        Что ожидаем: «аниме» и «про» отброшены, «котиков» свёрнут в «котик»
        и не повторяется дважды.
        """
        assert extract_terms("аниме про котиков, очень милых котиков") == [
            "котик",
            "очень",
            "милых",
        ]

    def test_extract_subject_terms_reads_explicit_topic(self):
        """Что тестируем: выделение явной темы запроса.
        Что передаём: запрос с предлогом «про» и запрос без темы.
        Что ожидаем: термы темы либо пустой список.
        """
        assert extract_subject_terms("аниме про котиков") == ["котик"]
        assert extract_subject_terms("посоветуй что-нибудь") == []


@pytest.mark.unit
class TestRecommendationPolicy:
    """Юнит-тесты правил оценки и сборки рекомендаций."""

    def test_build_search_plan_keeps_user_query_first(self):
        """Что тестируем: план поиска из запроса пользователя и вариантов модели.
        Что передаём: повтор запроса среди вариантов модели и пустую строку.
        Что ожидаем: уникальные варианты в исходном порядке с метками источника.
        """
        plan = build_search_plan(
            normalized_query="naruto dark",
            generated_queries=["naruto dark", "  ", "tragic shounen"],
        )

        assert plan == [
            {"query": "naruto dark", "source": "user_query"},
            {"query": "tragic shounen", "source": "ai_query"},
        ]

    def test_search_limit_grows_with_requested_count(self):
        """Что тестируем: размер выборки из каталога под нужное число рекомендаций.
        Что передаём: маленький и большой запросы.
        Что ожидаем: удвоение с нижним порогом — иначе фильтр съедает выдачу.
        """
        assert search_limit_for(2) == 8
        assert search_limit_for(10) == 20

    def test_score_candidate_prefers_explicit_subject(self):
        """Что тестируем: вес кандидата при явной теме запроса.
        Что передаём: тема «котик», двух кандидатов и жанр вкуса.
        Что ожидаем: тематический кандидат впереди, у чужого совпадений нет.
        """
        subject_terms = extract_subject_terms("аниме про котиков")
        kitten = score_candidate(
            KITTEN_ANIME,
            plan_index=0,
            query_terms=["котик"],
            variant_terms=["котик"],
            subject_terms=subject_terms,
            taste_genres=Counter(["Comedy"]),
        )
        sport = score_candidate(
            SPORT_ANIME,
            plan_index=0,
            query_terms=["котик"],
            variant_terms=["котик"],
            subject_terms=subject_terms,
            taste_genres=Counter(["Comedy"]),
        )

        assert kitten.subject_hits == 1
        assert kitten.topical_relevance == 1.0
        assert sport.subject_hits == 0
        assert kitten.score > sport.score
        assert kitten.genre_overlap == 1

    def test_score_candidate_downgrades_later_plan_variants(self):
        """Что тестируем: убывание веса по мере удаления от запроса пользователя.
        Что передаём: одного и того же кандидата на первом и третьем плане поиска.
        Что ожидаем: вариант пользователя весит больше, чем позднее расширение модели.
        """
        first = score_candidate(
            GENRE_ANIME,
            plan_index=0,
            query_terms=[],
            variant_terms=[],
            subject_terms=[],
            taste_genres=Counter(),
        )
        third = score_candidate(
            GENRE_ANIME,
            plan_index=2,
            query_terms=[],
            variant_terms=[],
            subject_terms=[],
            taste_genres=Counter(),
        )

        assert first.score > third.score

    def test_finalize_filters_candidates_off_topic(self):
        """Что тестируем: отсев кандидатов вне явной темы запроса.
        Что передаём: двух оценённых кандидатов и непустую тему.
        Что ожидаем: в выдаче остаётся только тот, кто совпал по теме.
        """
        on_topic = build_recommendation(
            GENRE_ANIME,
            CandidateScore(score=3.0, subject_hits=2, topical_relevance=1.0, genre_overlap=0),
            prompt="аниме про котиков",
            mode="hf_llm_text",
            query_source="user_query",
        )
        off_topic = build_recommendation(
            SPORT_ANIME,
            CandidateScore(score=5.0, subject_hits=0, topical_relevance=0.0, genre_overlap=1),
            prompt="аниме про котиков",
            mode="hf_llm_text",
            query_source="ai_query",
        )

        result = finalize_recommendations(
            [
                (
                    CandidateScore(
                        score=5.0, subject_hits=0, topical_relevance=0.0, genre_overlap=1
                    ),
                    off_topic,
                ),
                (
                    CandidateScore(
                        score=3.0, subject_hits=2, topical_relevance=1.0, genre_overlap=0
                    ),
                    on_topic,
                ),
            ],
            has_explicit_subject=True,
            subject_terms=["котик"],
            limit=5,
        )

        assert [item.anime_id for item in result] == [20]
        assert "Явная тема запроса совпала" in result[0].reason
        assert "Запрос разобран через AI" in result[0].reason

    def test_build_recommendation_falls_back_to_placeholders(self):
        """Что тестируем: карточку рекомендации для тайтла без названия и описания.
        Что передаём: карточку каталога с пустыми строками.
        Что ожидаем: запасной заголовок по идентификатору и адрес просмотра.
        """
        blank = Anime(external_id="33", title="", description=None)
        score = CandidateScore(
            score=1.23456, subject_hits=0, topical_relevance=0.0, genre_overlap=0
        )

        recommendation = build_recommendation(
            blank,
            score,
            prompt="что-то короткое",
            mode="fallback_no_token",
            query_source="ai_query",
        )

        assert recommendation.title == "Anime #33"
        assert recommendation.description == "Описание недоступно"
        assert recommendation.watch_url == "/watch/33?episode=1"
        assert recommendation.similarity_score == 1.235

    def test_taste_keywords_and_similarity_ignore_short_words(self):
        """Что тестируем: подбор по вкусу пользователя через описания его хайлайтов.
        Что передаём: описание хайлайта с короткими служебными словами.
        Что ожидаем: учитываются слова длиннее порога, вес нулевой без совпадения.
        """
        keywords = Counter(taste_keywords("basketball team fights"))
        matched = score_taste_similarity(
            SPORT_ANIME,
            taste_genres=Counter(["Sports"]),
            keyword_weights=keywords,
        )
        unmatched = score_taste_similarity(
            GENRE_ANIME,
            taste_genres=Counter(["Sports"]),
            keyword_weights=Counter({"zzzzzzzz": 1}),
        )

        assert "team" in keywords
        assert matched > 0
        assert unmatched == pytest.approx(0.082)
