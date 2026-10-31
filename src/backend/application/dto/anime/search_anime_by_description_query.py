"""Параметры запроса поиска аниме по описанию на естественном языке."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SearchAnimeByDescriptionQuery:
    """Параметры поиска аниме по свободному описанию.

    Attributes:
        description: Текст описания от пользователя.
        genre_hint: Подсказка по жанру, сужающая поиск.
        year_from: Нижняя граница года выхода.
        year_to: Верхняя граница года выхода.
        min_rating: Минимальный рейтинг результата.
        age_rating: Возрастное ограничение выдачи.
        adult_confirmed: Подтвердил ли пользователь показ взрослого контента.
        sort_by: Поле сортировки результатов.
        limit: Максимальное число результатов.
    """

    description: str
    genre_hint: str | None = None
    year_from: int | None = None
    year_to: int | None = None
    min_rating: int | None = None
    age_rating: str = "all"
    adult_confirmed: bool = False
    sort_by: str = "match"
    limit: int = 10
