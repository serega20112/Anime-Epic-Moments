"""Общие параметры постраничной выдачи хайлайтов для дашбордов."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HighlightDashboardQuery:
    """Фильтры и постраничная выдача для дашбордов хайлайтов.

    Attributes:
        anime_id: Фильтр по аниме.
        emotion: Фильтр по эмоции.
        category: Фильтр по категории.
        sort_by: Поле сортировки.
        created_date: Фильтр по дате создания.
        query: Поисковая строка по заголовку и описанию.
        include_spoilers: Показывать ли спойлеры.
        limit: Максимальное число записей.
        user_id: Владелец личного дашборда: автор хайлайтов или зритель подписок.
        viewer_user_id: Идентификатор зрителя для отметок лайков и сохранений.
    """

    anime_id: int | None = None
    emotion: str | None = None
    category: str | None = None
    sort_by: str = "recent"
    created_date: str | None = None
    query: str | None = None
    include_spoilers: bool = False
    limit: int = 20
    user_id: int | None = None
    viewer_user_id: int | None = None
