"""Единый контракт постраничной выдачи JSON API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Page[T](BaseModel):
    """Одна страница коллекции с метаданными навигации.

    Единица контракта пагинации для всех лент и каталогов: клиент читает
    навигацию из этих полей и не строит её сам по длине ``items``. Модель
    принимает доменные объекты напрямую (``from_attributes``), поэтому маршрут
    не собирает словарь ответа вручную.

    Attributes:
        items: Элементы запрошенной страницы.
        page: Номер страницы, начиная с единицы.
        per_page: Размер страницы, использованный при выборке.
        total: Общее число элементов, удовлетворяющих фильтру.
        total_pages: Число страниц при текущем фильтре, не меньше одной.
        has_next: Есть ли страница после текущей.
        has_previous: Есть ли страница перед текущей.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool


def as_single_page[T](items: list[T]) -> dict[str, object]:
    """Обернуть всю выборку в единый конверт страницы.

    Используется там, где сценарий возвращает список целиком и не поддерживает
    нарезку: вся выборка идёт первой и единственной страницей, чтобы клиент
    читал навигацию из общего контракта, а не по длине ``items``.

    Args:
        items: Элементы всей выборки.

    Returns:
        dict[str, object]: Поля конверта для конструктора ``Page``.
    """
    total = len(items)
    return {
        "items": items,
        "page": 1,
        "per_page": total or 1,
        "total": total,
        "total_pages": 1,
        "has_next": False,
        "has_previous": False,
    }
