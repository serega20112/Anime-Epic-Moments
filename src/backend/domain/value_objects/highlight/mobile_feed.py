"""Страница ленты хайлайтов для мобильного клиента с пагинацией.

Отличие от веба: мобильный контракт читает ровно одну последовательность карточек
и поля навигации, а режимы ленты (для вас, подписки, топ) переключает сценарий.
Нарезка окна и подсчёт общего числа делаются в прикладном слое, поэтому
presentation остаётся тонким.
"""

from dataclasses import dataclass

from backend.domain.value_objects.highlight.cards import HighlightCard


@dataclass(frozen=True)
class MobileHighlightFeedPage:
    """Одна страница ленты хайлайтов с метаданными навигации.

    Attributes:
        items: Карточки текущей страницы.
        page: Номер страницы, начиная с единицы.
        per_page: Размер страницы.
        total: Общее число карточек в выбранном режиме.
        total_pages: Число страниц, не меньше одной.
        has_next: Есть ли страница после текущей.
        has_previous: Есть ли страница перед текущей.
    """

    items: list[HighlightCard]
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool
