"""Значимый объект оценки кандидата в рекомендации."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CandidateScore:
    """Балл релевантности кандидата и составляющие, из которых он сложен.

    Attributes:
        score: Итоговый балл упорядочивания.
        subject_hits: Число совпадений явной темы запроса.
        topical_relevance: Лучшая релевантность по смыслу запроса.
        genre_overlap: Число совпавших жанров с избранным пользователя.
    """

    score: float
    subject_hits: int
    topical_relevance: float
    genre_overlap: int
