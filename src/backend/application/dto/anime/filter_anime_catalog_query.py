"""Параметры запроса каталога аниме с фильтрами в стиле Anixart."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.domain.value_objects.anime.genre_filter import GenreMatchMode


@dataclass(frozen=True, slots=True)
class FilterAnimeCatalogQuery:
    """Набор фильтров и настроек выдачи для страницы каталога.

    Attributes:
        genres: Выбранные жанры; пустое значение означает «все жанры».
        genre_mode: Правило объединения жанров: все сразу или любой из них.
        media_type: Тип произведения (сериал, фильм и так далее).
        status: Статус выхода аниме.
        has_dub: True — только с озвучкой, False — только без неё, None — не важно.
        year_from: Нижняя граница года выхода.
        year_to: Верхняя граница года выхода.
        min_score: Минимальный рейтинг от нуля до десяти.
        sort: Поле сортировки.
        order: Направление сортировки.
        page: Номер запрошенной страницы.
        per_page: Размер страницы.
    """

    genres: tuple[str, ...] = field(default_factory=tuple)
    genre_mode: GenreMatchMode = GenreMatchMode.ALL
    media_type: str = ""
    status: str = ""
    has_dub: bool | None = None
    year_from: int | None = None
    year_to: int | None = None
    min_score: float | None = None
    sort: str = "rating"
    order: str = "desc"
    page: int = 1
    per_page: int = 25
