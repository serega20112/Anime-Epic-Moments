"""Фильтрация каталога через AniList.

AniList не умеет отдавать жанры и свободные теги одним запросом, поэтому
каталог собирается из одного или двух запросов и досортировывается локально.
Логика вынесена из клиента: она про правила выдачи, а не про транспорт.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import httpx

from backend.domain.entities.anime.anime import Anime
from backend.domain.value_objects.anime.catalog_page import CatalogPage
from backend.infrastructure.external.catalog.anilist_queries import catalog_query, split_genres
from backend.infrastructure.external.catalog.mapping import build_anime_from_anilist_item


class AniListCatalogMixin:
    """Умеет фильтровать каталог запросами к AniList.

    Рассчитан на использование в клиенте AniList: обращается к его
    ``session`` и ``base_url``.
    """

    session: httpx.AsyncClient
    base_url: str

    async def filter_catalog(
        self,
        *,
        genres: Sequence[str] = (),
        media_type: str = "",
        status: str = "",
        year_from: int | None = None,
        year_to: int | None = None,
        min_score: float | None = None,
        sort: str = "rating",
        order: str = "desc",
        page: int = 1,
        per_page: int = 25,
    ) -> CatalogPage:
        """Фильтрует и сортирует каталог запросом к AniList.

        Args:
            genres: Жанры и теги, по которым сужается каталог.
            media_type: Нормализованный формат тайтла.
            status: Нормализованный статус выхода.
            year_from: Нижняя граница года выпуска.
            year_to: Верхняя граница года выпуска.
            min_score: Минимальный рейтинг в шкале 0–10.
            sort: Ключ сортировки.
            order: Направление сортировки (asc, desc).
            page: Номер страницы, начиная с единицы.
            per_page: Размер страницы.

        Returns:
            CatalogPage: Запрошенная страница каталога; пустая при сбое.
        """
        selected_genres, selected_tags = split_genres(genres)
        direction = "asc" if str(order).strip().lower() == "asc" else "desc"

        async def run_query(use_genres: bool, use_tags: bool) -> tuple[list[Anime], int]:
            """Выполнить запрос каталога с указанными фильтрами.

            Args:
                use_genres: Применять ли фильтр по жанрам.
                use_tags: Применять ли фильтр по тегам.

            Returns:
                tuple[list[Anime], int]: Смэпленные тайтлы и общее число
                совпадений.
            """
            query, variables = catalog_query(
                genres=selected_genres,
                tags=selected_tags,
                include_genres=use_genres,
                include_tags=use_tags,
                media_type=media_type,
                status=status,
                year_from=year_from,
                year_to=year_to,
                min_score=min_score,
                sort=sort,
                order=order,
                page=page,
                per_page=per_page,
            )
            try:
                resp = await self.session.post(
                    self.base_url,
                    json={"query": query, "variables": variables},
                )
                resp.raise_for_status()
                payload = resp.json().get("data", {}).get("Page", {})
                data = payload.get("media", []) or []
                total = int(payload.get("pageInfo", {}).get("total") or 0)
            except (httpx.HTTPError, ValueError, KeyError, TypeError):
                return [], 0

            result = []
            for item in data:
                result.append(
                    await build_anime_from_anilist_item(item, fallback_to_anilist_id=True)
                )
            return result, total

        if selected_genres and selected_tags:
            merged, total = await run_query(True, False)
            seen = {(item.external_id or "", item.title) for item in merged}
            tags_only, _ = await run_query(False, True)
            for item in tags_only:
                if (item.external_id or "", item.title) not in seen:
                    seen.add((item.external_id or "", item.title))
                    merged.append(item)
            ordered = self._sort_catalog_items(merged, sort, direction)
            start = (max(1, int(page)) - 1) * int(per_page)
            return CatalogPage.build(
                ordered[start : start + int(per_page)],
                page=page,
                per_page=per_page,
                total=max(total, start + len(merged)),
            )
        if selected_genres:
            items, total = await run_query(True, False)
        elif selected_tags:
            items, total = await run_query(False, True)
        else:
            items, total = await run_query(False, False)
        return CatalogPage.build(items, page=page, per_page=per_page, total=total)

    @staticmethod
    def _sort_catalog_items(items: list[Anime], sort: str, direction: str) -> list[Anime]:
        """Пересортировать склеенную выдачу нескольких запросов.

        Args:
            items: Смэпленные тайтлы.
            sort: Нормализованный ключ сортировки.
            direction: Направление сортировки (asc, desc).

        Returns:
            list[Anime]: Отсортированный список.
        """
        reverse = direction != "asc"

        def by_year(anime: Anime) -> float:
            """Ключ сортировки по году выхода."""
            return anime.year or 0

        def by_title(anime: Anime) -> str:
            """Ключ сортировки по названию без учёта регистра."""
            return (anime.title or "").lower()

        def by_rating(anime: Anime) -> float:
            """Ключ сортировки по рейтингу."""
            return anime.rating or 0

        key: Callable[[Anime], Any]
        if sort == "newest":
            key = by_year
        elif sort == "title":
            key = by_title
        else:
            key = by_rating
        return sorted(items, key=key, reverse=reverse)
