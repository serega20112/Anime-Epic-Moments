"""Фасад над каталогами Jikan и AniList.

Клиент владеет общим HTTP-сеансом, кэшем и правилами фолбэка: Jikan — основной
источник карточек, AniList подстраховывает его, Shikimori подмешивает русские
названия. Транспорт каждого провайдера живёт в своём клиенте, кэш — в
:mod:`anime_api_cache`, гонка источников — в ``external._common.race``.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

import httpx

from backend.application.interface.services.anime_api_client import AnimeApiClientInterface
from backend.domain.entities.anime.anime import Anime
from backend.domain.value_objects.anime.catalog_page import CatalogPage
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.external._common.race import first_catalog_page, first_truthy
from backend.infrastructure.external.catalog.anilist_client import (
    AniListAnimeClient,
    AniListSearchError,
)
from backend.infrastructure.external.catalog.anime_api_cache import CACHE_MISS, AnimeApiCache
from backend.infrastructure.external.catalog.jikan_client import JikanAnimeClient
from backend.infrastructure.external.catalog.mapping import passes_filters, sanitize_query
from backend.infrastructure.external.catalog.shikimori_client import ShikimoriClient

logger = logging.getLogger("anime_epic_moments")


class AnimeApiClient(AnimeApiClientInterface):
    """Отдаёт карточки аниме из Jikan и AniList с кэшированием.

    Провайдерские сетевые вызовы делегируются :class:`JikanAnimeClient` и
    :class:`AniListAnimeClient`; маппинг payload'а в домен выполняют чистые
    функции границы слоя. Наследование порта проверено статически: без него
    сценарий мог бы вызывать метод, которого у подмены клиента нет.
    """

    def __init__(self, store: KeyValueStore | None = None):
        """Инициализирует клиент.

        Args:
            store: Хранилище кэша; при None создаётся локальное без Redis.
        """
        self.store = store or KeyValueStore(redis_url=None, namespace="anime_api")
        self._cache = AnimeApiCache(self.store)
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=3.0, read=6.0, write=3.0, pool=3.0),
            trust_env=False,
        )
        self.jikan = JikanAnimeClient(self.session)
        self.anilist = AniListAnimeClient(self.session)
        self.shikimori = ShikimoriClient(self.session, self.store)

    @property
    def jikan_base(self) -> str:
        """Базовый URL Jikan (для самопроверки и тестов).

        Returns:
            str: Базовый URL API Jikan.
        """
        return self.jikan.base_url

    @property
    def anilist_base(self) -> str:
        """Базовый URL GraphQL AniList (для самопроверки и тестов).

        Returns:
            str: Базовый URL GraphQL AniList.
        """
        return self.anilist.base_url

    @property
    def genre_id_map(self) -> dict[str, int]:
        """Карта жанров Jikan (сохранена для обратной совместимости).

        Returns:
            dict[str, int]: Соответствие названия жанра его id в Jikan.
        """
        return self.jikan.genre_id_map

    async def aclose(self) -> None:
        """Закрывает общий HTTP-клиент."""
        await self.session.aclose()

    async def search_by_title(
        self, title: str, limit: int = 10, include_adult: bool = False
    ) -> list[Anime]:
        """Ищет аниме по названию, подстраховываясь AniList.

        Args:
            title: Поисковый запрос.
            limit: Максимальное число результатов.
            include_adult: Разрешён ли взрослый контент.

        Returns:
            list[Anime]: Найденные тайтлы.
        """
        sanitized_title = await sanitize_query(title)
        if not sanitized_title:
            return []
        cache_key = await self._cache.key(
            "search_by_title_v2",
            sanitized_title.lower(),
            int(limit),
            int(bool(include_adult)),
        )
        cached = await self._cache.get(cache_key)
        if cached is not CACHE_MISS:
            return list(cached)
        result = await self.jikan.search_by_title(
            sanitized_title,
            limit=limit,
            include_adult=include_adult,
        )
        if result:
            enriched = await self._enrich_with_russian(result)
            return list(await self._cache.set(cache_key, enriched, ttl_seconds=300))
        result = await self.anilist.search_by_title(
            title=sanitized_title,
            limit=limit,
            include_adult=include_adult,
        )
        ttl_seconds = 300 if result else 60
        enriched = await self._enrich_with_russian(result)
        return list(await self._cache.set(cache_key, enriched, ttl_seconds=ttl_seconds))

    async def get_season_popular(self, year: int, season: str, limit: int = 10) -> list[Anime]:
        """Возвращает популярные тайтлы сезона, подстраховываясь AniList.

        Args:
            year: Год сезона.
            season: Название сезона (winter, spring, summer, fall).
            limit: Максимальное число результатов.

        Returns:
            list[Anime]: Сезонная подборка.
        """
        cache_key = await self._cache.key(
            "season_popular",
            int(year),
            str(season).strip().lower(),
            int(limit),
        )
        cached = await self._cache.get(cache_key)
        if cached is not CACHE_MISS:
            return list(cached)
        result = await self.jikan.get_season_popular(year, season, limit)
        if result:
            enriched = await self._enrich_with_russian(result)
            return list(await self._cache.set(cache_key, enriched, ttl_seconds=900))
        result = await self.anilist.get_season_popular(year=year, season=season, limit=limit)
        ttl_seconds = 900 if result else 60
        enriched = await self._enrich_with_russian(result)
        return list(await self._cache.set(cache_key, enriched, ttl_seconds=ttl_seconds))

    async def search_by_description(
        self,
        description: str,
        year_from: int | None = None,
        year_to: int | None = None,
        min_rating: int | None = None,
        include_adult: bool = False,
        limit: int = 10,
    ) -> list[Anime]:
        """Ищет аниме по свободному описанию через GraphQL AniList.

        Когда AniList недоступен, поиск деградирует в поиск по названию.

        Args:
            description: Описание аниме на естественном языке.
            year_from: Нижняя граница года выпуска.
            year_to: Верхняя граница года выпуска.
            min_rating: Минимальный нормализованный рейтинг.
            include_adult: Разрешён ли взрослый контент.
            limit: Максимальное число результатов.

        Returns:
            list[Anime]: Найденные тайтлы.
        """
        sanitized_description = await sanitize_query(description)
        if not sanitized_description:
            return []
        cache_key = await self._cache.key(
            "search_by_description",
            sanitized_description.lower(),
            year_from if year_from is not None else "",
            year_to if year_to is not None else "",
            min_rating if min_rating is not None else "",
            int(bool(include_adult)),
            int(limit),
        )
        cached = await self._cache.get(cache_key)
        if cached is not CACHE_MISS:
            return list(cached)
        try:
            items = await self.anilist.search_by_description(
                description=sanitized_description,
                limit=limit,
                include_adult=include_adult,
            )
        except AniListSearchError:
            fallback = await self.search_by_title(
                title=sanitized_description, limit=limit, include_adult=include_adult
            )
            return list(await self._cache.set(cache_key, fallback, ttl_seconds=300))
        result = []
        for anime in items:
            if not await passes_filters(
                season_year=anime.year,
                normalized_score=anime.rating,
                year_from=year_from,
                year_to=year_to,
                min_rating=min_rating,
            ):
                continue
            result.append(anime)
            if len(result) >= limit:
                break
        enriched = await self._enrich_with_russian(result)
        return list(await self._cache.set(cache_key, enriched, ttl_seconds=300))

    async def get_by_id(self, anime_id: int) -> Anime | None:
        """Возвращает аниме по идентификатору, гоняя Jikan и AniList.

        Гонка нужна из-за зависаний Jikan: пока один источник ждёт таймаут,
        второй успевает отдать карточку.

        Args:
            anime_id: Идентификатор аниме.

        Returns:
            Anime | None: Карточка аниме или None, если её нет ни в одном
            источнике.
        """
        anime_id = int(anime_id)
        cache_key = await self._cache.key("anime", anime_id)
        cached = await self._cache.get(cache_key)
        if cached is not CACHE_MISS:
            return cached
        result = await first_truthy(
            self.jikan.get_by_id(anime_id),
            self._get_by_anilist_id(anime_id),
            self._get_by_anilist_mal_id(anime_id),
        )
        if result is not None:
            result = (await self._enrich_with_russian([result]))[0]
        return await self._cache.set(cache_key, result, ttl_seconds=1800)

    async def _get_by_anilist_id(self, anime_id: int) -> Anime | None:
        """Возвращает аниме по id AniList как фолбэк.

        Args:
            anime_id: Идентификатор аниме в AniList.

        Returns:
            Anime | None: Карточка аниме или None, если её нет.
        """
        return await self.anilist.get_by_anilist_id(anime_id)

    async def _get_by_anilist_mal_id(self, anime_id: int) -> Anime | None:
        """Возвращает аниме по id MyAnimeList как дополнительный фолбэк.

        Один и тот же идентификатор может быть как id AniList, так и id
        MyAnimeList — зависит от источника, который построил карточку: Jikan
        отдаёт MAL-идентификаторы, AniList — значения ``idMal``. Разрешение
        через ``idMal`` покрывает случай, когда Jikan недоступен.

        Args:
            anime_id: Идентификатор аниме в MyAnimeList.

        Returns:
            Anime | None: Карточка аниме или None, если её нет.
        """
        return await self.anilist.get_by_mal_id(anime_id)

    async def get_top_anime(self, limit: int = 25) -> list[Anime]:
        """Возвращает популярные тайтлы через top-эндпоинт Jikan.

        Args:
            limit: Максимальное число результатов.

        Returns:
            list[Anime]: Популярные тайтлы.
        """
        cache_key = await self._cache.key("top", int(limit))
        cached = await self._cache.get(cache_key)
        if cached is not CACHE_MISS:
            return list(cached)
        result = await self.jikan.get_top_anime(limit)
        enriched = await self._enrich_with_russian(result)
        return list(await self._cache.set(cache_key, enriched, ttl_seconds=900))

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
        """Выдаёт каталог с фильтрами, гоняя Jikan и AniList.

        Args:
            genres: Жанры и теги, по которым сужается каталог.
            media_type: Формат тайтла (tv, movie, ova, ona, special); пусто —
                все форматы.
            status: Статус выхода (airing, complete, upcoming); пусто — все.
            year_from: Нижняя граница года выпуска.
            year_to: Верхняя граница года выпуска.
            min_score: Минимальный нормализованный рейтинг (0–10).
            sort: Стратегия сортировки (rating, popularity, newest, title).
            order: Направление сортировки (asc, desc).
            page: Номер страницы, начиная с единицы.
            per_page: Размер страницы.

        Returns:
            CatalogPage: Страница каталога с метаданными пагинации.
        """
        sort_key = sort
        valid_sorts = {"rating", "popularity", "newest", "title"}
        if sort_key not in valid_sorts:
            sort_key = "rating"
        order_key = "asc" if str(order).strip().lower() == "asc" else "desc"
        normalized_genres = tuple(str(name).strip() for name in genres if str(name).strip())
        page_number = max(1, int(page))
        page_size = max(1, int(per_page))
        cache_key = await self._cache.key(
            "filter_catalog_v2",
            "|".join(sorted(normalized_genres)),
            str(media_type).strip().lower(),
            str(status).strip().lower(),
            year_from if year_from is not None else "",
            year_to if year_to is not None else "",
            min_score if min_score is not None else "",
            sort_key,
            order_key,
            page_number,
            page_size,
        )
        cached = await self._cache.get(cache_key)
        if cached is not CACHE_MISS:
            return await self._cache.page(cached, page_number, page_size)

        result = await first_catalog_page(
            self.jikan.filter_catalog(
                genres=normalized_genres,
                media_type=media_type,
                status=status,
                year_from=year_from,
                year_to=year_to,
                min_score=min_score,
                sort=sort_key,
                order=order_key,
                page=page_number,
                per_page=page_size,
            ),
            self.anilist.filter_catalog(
                genres=normalized_genres,
                media_type=media_type,
                status=status,
                year_from=year_from,
                year_to=year_to,
                min_score=min_score,
                sort=sort_key,
                order=order_key,
                page=page_number,
                per_page=page_size,
            ),
        )
        ttl_seconds = 600 if len(result.items) else 60
        enriched = await self._enrich_with_russian(list(result.items))
        await self._cache.set(
            cache_key,
            {"items": enriched, "total": result.total},
            ttl_seconds=ttl_seconds,
        )
        return CatalogPage.build(enriched, page=page_number, per_page=page_size, total=result.total)

    async def _enrich_with_russian(self, animes: list[Anime]) -> list[Anime]:
        """Подставляет русские названия и описания из Shikimori.

        Числовые MAL-идентификаторы собираются в один запрос; русское
        значение становится ``title``/``description``, а исходное название
        уезжает в ``original_title``. Любой сбой оставляет карточку как есть.

        Args:
            animes: Карточки, которые нужно обогатить (меняются на месте).

        Returns:
            list[Anime]: Тот же список с подставленными русскими полями.
        """
        if not animes:
            return animes
        batched: dict[int, Anime] = {}
        for anime in animes:
            if not anime.external_id or not str(anime.external_id).strip().isdigit():
                continue
            batched.setdefault(int(anime.external_id), anime)
        if not batched:
            return animes
        try:
            russian_map = await self.shikimori.fetch_russian(list(batched))
        except Exception as error:
            logger.warning("shikimori enrichment skipped reason=%s", error.__class__.__name__)
            return animes
        for mal_id, anime in batched.items():
            russian_title, russian_desc = russian_map.get(mal_id, (None, None))
            if russian_title and russian_title != anime.title:
                if not anime.original_title:
                    anime.original_title = anime.title if anime.title else None
                anime.title = russian_title
            if russian_desc:
                anime.description = russian_desc
        return animes
