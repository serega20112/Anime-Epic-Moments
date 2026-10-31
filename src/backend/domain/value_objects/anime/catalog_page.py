"""Значимый объект страницы каталога с метаданными пагинации."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from backend.domain.entities.anime.anime import Anime


@dataclass(frozen=True, slots=True)
class CatalogPage:
    """Часть выдачи каталога вместе с состоянием пагинации."""

    items: tuple[Anime, ...]
    page: int
    per_page: int
    total: int
    total_is_exact: bool = True

    @classmethod
    def build(
        cls,
        items: Sequence[Anime],
        *,
        page: int,
        per_page: int,
        total: int,
        total_is_exact: bool = True,
    ) -> CatalogPage:
        """Собрать страницу с нормализацией номера и общего числа."""
        return cls(
            items=tuple(items),
            page=max(1, int(page)),
            per_page=max(1, int(per_page)),
            total=max(0, int(total)),
            total_is_exact=total_is_exact,
        )

    @property
    def total_pages(self) -> int:
        """Число страниц, на которые делится каталог.

        Returns:
            int: Общее число страниц, минимум одна.
        """
        if self.total <= 0:
            return 1
        return max(1, math.ceil(self.total / self.per_page))

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

    def __len__(self) -> int:
        """Вернуть число элементов на странице."""
        return len(self.items)
