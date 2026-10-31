"""Страница каталога аниме вместе со счётчиками для панели фильтров."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.domain.entities.anime.anime import Anime
from backend.domain.value_objects.anime.genre_facet import GenreFacet


@dataclass(frozen=True, slots=True)
class AnimeCatalogResult:
    """Одна страница каталога вместе с метаданными для интерфейса.

    Attributes:
        items: Аниме, попавшие на запрошенную страницу.
        page: Номер поданной страницы, начиная с единицы.
        per_page: Размер страницы, использованный при выборке.
        total: Общее число записей, удовлетворяющих фильтру.
        total_is_exact: True, если ``total`` подсчитан точно, а не оценочно.
        genre_facets: Счётчики по жанрам для панели фильтров.
    """

    items: tuple[Anime, ...] = field(default_factory=tuple)
    page: int = 1
    per_page: int = 25
    total: int = 0
    total_is_exact: bool = True
    genre_facets: tuple[GenreFacet, ...] = field(default_factory=tuple)

    @property
    def total_pages(self) -> int:
        """Сколько всего страниц даёт текущий фильтр.

        Returns:
            int: Число страниц, не меньше одной.
        """
        if self.total <= 0:
            return 1
        return max(1, -(-self.total // self.per_page))

    @property
    def has_next(self) -> bool:
        """Есть ли страница после текущей.

        Returns:
            bool: True, если текущая страница не последняя.
        """
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """Есть ли страница перед текущей.

        Returns:
            bool: True, если текущая страница не первая.
        """
        return self.page > 1
