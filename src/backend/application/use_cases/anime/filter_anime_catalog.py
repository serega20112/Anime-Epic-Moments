"""Сценарий просмотра каталога аниме с фильтрами в стиле Anixart."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

from backend.application.dto.anime import AnimeCatalogResult, FilterAnimeCatalogQuery
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.services import (
    AnimeApiClientInterface,
    WatchSourceSyncServiceInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain.entities.anime.anime import Anime
from backend.domain.exceptions import ExternalServiceError
from backend.domain.value_objects.anime.genre_facet import GenreFacet
from backend.domain.value_objects.anime.genre_filter import (
    GenreFilter,
    GenreMatchMode,
    normalize_genre,
)

DEFAULT_PER_PAGE = 25
ALLOWED_PER_PAGE = (10, 25, 50, 100)
FACET_LIMIT = 60
DUB_FETCH_MULTIPLIER = 4
WINDOW_LIMIT = 400

logger = logging.getLogger("anime_epic_moments")


def build_facets(animes: Sequence[Anime]) -> tuple[GenreFacet, ...]:
    """Посчитать жанры по просмотренным тайтлам, начиная с самых частых.

    Args:
        animes: Тайтлы, отданные провайдером в окне выборки.

    Returns:
        tuple[GenreFacet, ...]: Жанры с числом вхождений, от частых к редким.
    """
    counters: dict[str, int] = {}
    labels: dict[str, str] = {}
    for anime in animes:
        for genre in getattr(anime, "genres", None) or ():
            label = str(genre).strip()
            key = normalize_genre(label)
            if not key:
                continue
            counters[key] = counters.get(key, 0) + 1
            labels.setdefault(key, label)
    ordered = sorted(counters.items(), key=lambda item: (-item[1], item[0]))
    return tuple(GenreFacet(name=labels[key], count=count) for key, count in ordered[:FACET_LIMIT])


class FilterAnimeCatalogUseCase:
    """Фильтрует каталог аниме в стиле Anixart.

    Провайдеры сужают каталог только по ИЛИ-семантике, поэтому точные смыслы
    выбора жанров (все выбранные или любой из них) применяются здесь через
    :class:`GenreFilter`. Список можно ограничить тайтлами с озвучкой: сначала
    это проверяется по локальной таблице переводов, а затем по карте
    доступности провайдера.
    """

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        api_client: AnimeApiClientInterface,
        watch_source_sync_service: WatchSourceSyncServiceInterface,
    ) -> None:
        """Инициализирует сценарий фильтрации каталога аниме.

        Args:
            unit_of_work: Граница транзакции чтения локальных переводов.
            api_client: Клиент API аниме.
            watch_source_sync_service: Сервис доступности озвучек у провайдеров.
        """
        self._unit_of_work = unit_of_work
        self._api_client = api_client
        self._watch_source_sync_service = watch_source_sync_service

    async def execute(self, query: FilterAnimeCatalogQuery) -> AnimeCatalogResult:
        """Возвращает страницу каталога по запрошенным фильтрам.

        Args:
            query: Фильтры, сортировка и номер страницы.

        Returns:
            AnimeCatalogResult: Запрошенная страница, метаданные пагинации и
                жанры, встреченные в просмотренной выдаче.
        """
        per_page = self._per_page(query.per_page)
        genre_filter = GenreFilter.from_values(query.genres, query.genre_mode)
        needs_window = query.has_dub is True or genre_filter.mode is GenreMatchMode.ALL

        if needs_window:
            return await self._execute_over_window(query, genre_filter, per_page)

        page = await self._api_client.filter_catalog(
            genres=query.genres,
            media_type=query.media_type,
            status=query.status,
            year_from=query.year_from,
            year_to=query.year_to,
            min_score=query.min_score,
            sort=query.sort,
            order=query.order,
            page=query.page,
            per_page=per_page,
        )
        items = [anime for anime in page.items if genre_filter.matches(anime.genres)]
        return AnimeCatalogResult(
            items=tuple(items),
            page=page.page,
            per_page=page.per_page,
            total=page.total,
            total_is_exact=True,
            genre_facets=build_facets(page.items),
        )

    async def _execute_over_window(
        self,
        query: FilterAnimeCatalogQuery,
        genre_filter: GenreFilter,
        per_page: int,
    ) -> AnimeCatalogResult:
        """Сузить увеличенное окно провайдера локальными фильтрами.

        Провайдеры не умеют конъюнкцию жанров и признак озвучки, поэтому широкое
        окно читается один раз и сужается на месте.

        Args:
            query: Фильтры и номер страницы.
            genre_filter: Точный смысл совпадения по жанрам.
            per_page: Приведённый размер страницы.

        Returns:
            AnimeCatalogResult: Запрошенная страница суженного окна.
        """
        window = self._window_size(query.page, per_page, query.has_dub is True)
        provider_page = await self._api_client.filter_catalog(
            genres=query.genres,
            media_type=query.media_type,
            status=query.status,
            year_from=query.year_from,
            year_to=query.year_to,
            min_score=query.min_score,
            sort=query.sort,
            order=query.order,
            page=1,
            per_page=window,
        )
        scanned = list(provider_page.items)

        candidates = [anime for anime in scanned if genre_filter.matches(anime.genres)]
        if query.has_dub is True and candidates:
            candidates = await self._keep_dubbed(candidates)

        start = (max(1, query.page) - 1) * per_page
        return AnimeCatalogResult(
            items=tuple(candidates[start : start + per_page]),
            page=max(1, query.page),
            per_page=per_page,
            total=len(candidates),
            total_is_exact=len(scanned) < window,
            genre_facets=build_facets(scanned),
        )

    @staticmethod
    def _per_page(value: int) -> int:
        """Привести запрошенный размер страницы к ближайшему допустимому.

        Args:
            value: Значение размера страницы из запроса.

        Returns:
            int: Размер из разрешённого набора либо значение по умолчанию.
        """
        try:
            requested = int(value)
        except (TypeError, ValueError):
            return DEFAULT_PER_PAGE
        if requested in ALLOWED_PER_PAGE:
            return requested
        return min(ALLOWED_PER_PAGE, key=lambda size: abs(size - requested))

    @staticmethod
    def _window_size(page: int, per_page: int, needs_dub: bool) -> int:
        """Посчитать, сколько записей провайдера нужно просмотреть ради страницы.

        Args:
            page: Запрошенный номер страницы.
            per_page: Приведённый размер страницы.
            needs_dub: Нужна ли фильтрация по наличию озвучки.

        Returns:
            int: Размер окна выборки провайдера в пределах безопасного лимита.
        """
        required = max(1, page) * per_page
        if needs_dub:
            required *= DUB_FETCH_MULTIPLIER
        return min(WINDOW_LIMIT, max(per_page, required))

    async def _keep_dubbed(self, candidates: Sequence[Anime]) -> list[Anime]:
        """Оставить только тайтлы, у которых есть хотя бы одна озвучка.

        Args:
            candidates: Тайтлы, прошедшие жанровый фильтр.

        Returns:
            list[Anime]: Тайтлы с подтверждённой доступностью озвучки.
        """
        flags = await self._local_dub_flags(candidates)
        unresolved = [anime for anime, dubbed in zip(candidates, flags, strict=True) if not dubbed]
        remote_flags = await asyncio.gather(
            *(self._has_provider_translation(anime) for anime in unresolved)
        )
        merged = list(flags)
        positions = [index for index, dubbed in enumerate(flags) if not dubbed]
        for position, dubbed in zip(positions, remote_flags, strict=True):
            merged[position] = dubbed
        return [anime for anime, dubbed in zip(candidates, merged, strict=True) if dubbed]

    async def _local_dub_flags(self, candidates: Sequence[Anime]) -> list[bool]:
        """Проверить наличие озвучки в локальной базе одной транзакцией.

        Захват широкий намеренно: это вспомогательная проверка доступности, и
        сбой базы не должен ронять выдачу каталога целиком. Случай не
        проглатывается: он уходит в лог уровнем ERROR со stack trace, чтобы баг
        кода не выглядел штатной пустой озвучкой.

        Args:
            candidates: Тайтлы для проверки.

        Returns:
            list[bool]: Признаки озвучки в том же порядке, что и тайтлы.
        """
        flags: list[bool] = []
        async with self._unit_of_work as uow:
            repository = uow.repository(WatchRepository)
            for anime in candidates:
                anime_id = anime.mal_id
                if anime_id is None:
                    flags.append(False)
                    continue
                try:
                    translations = await repository.get_translations(anime_id=anime_id)
                except Exception:
                    logger.exception(
                        "catalog_local_translation_lookup_failed anime_id=%s", anime_id
                    )
                    translations = []
                flags.append(bool(translations))
        return flags

    async def _has_provider_translation(self, anime: Anime) -> bool:
        """Проверить озвучку тайтла по карте доступности провайдера.

        Штатный сбой провайдера (`ExternalServiceError`) — это деградация на
        warning: озвучка просто не подтверждена. Любой другой исключительный
        случай уходит в лог со stack trace, чтобы баг кода не прятался за
        пустой выдачей каталога.

        Args:
            anime: Тайтл без локально найденных переводов.

        Returns:
            bool: True, если провайдер сообщает хотя бы об одной озвучке.
        """
        if not anime.title:
            return False
        try:
            availability = await self._watch_source_sync_service.get_translations_availability(
                title=anime.title,
                year=anime.year,
                shikimori_id=anime.mal_id,
                genres=anime.genres,
            )
            return bool(availability)
        except ExternalServiceError as error:
            logger.warning(
                "catalog_provider_availability_lookup_failed title=%s reason=%s",
                anime.title,
                error.__class__.__name__,
            )
            return False
        except Exception:
            logger.exception("catalog_provider_availability_lookup_failed title=%s", anime.title)
            return False
