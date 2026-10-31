"""Клиент AniList: транспорт GraphQL и разбор ответа.

Клиент только ходит в AniList и делегирует маппинг чистым функциям
``catalog.mapping``. Сборка запросов живёт в :mod:`anilist_queries`, фильтры
каталога — в :mod:`anilist_catalog`.
"""

from __future__ import annotations

import httpx

from backend.domain.entities.anime.anime import Anime
from backend.infrastructure.external._common import ExternalServiceError
from backend.infrastructure.external.catalog.anilist_catalog import AniListCatalogMixin
from backend.infrastructure.external.catalog.anilist_queries import (
    ANILIST_BASE_URL,
    ANILIST_GENRES,
    media_query,
    search_query,
    season_popular_query,
)
from backend.infrastructure.external.catalog.mapping import (
    build_anime_from_anilist_item,
    is_nsfw_anilist,
)

__all__ = ["ANILIST_BASE_URL", "ANILIST_GENRES", "AniListAnimeClient", "AniListSearchError"]


class AniListSearchError(ExternalServiceError):
    """Ошибка сетевого слоя при поиске AniList по описанию.

    Остальные методы AniList деградируют в пустой результат, потому что
    участвуют в гонке источников и в фолбэках. Поиск по описанию — наоборот,
    сообщает о сбое явно, чтобы оркестратор перешёл к поиску по названию.
    """

    service_name = "anilist"


class AniListAnimeClient(AniListCatalogMixin):
    """Клиент GraphQL API AniList.

    Ходит в сеть и отдаёт доменные объекты; маппинг payload'а выполняют
    чистые функции. Большинство методов на сбое возвращают пустой результат,
    и только :meth:`search_by_description` бросает :class:`AniListSearchError`.
    """

    def __init__(self, session: httpx.AsyncClient, base_url: str = ANILIST_BASE_URL):
        """Инициализирует клиент.

        Args:
            session: Общий HTTP-клиент, которым владеет фасад-оркестратор.
            base_url: Базовый URL GraphQL API AniList.
        """
        self.session = session
        self.base_url = base_url

    async def search_by_title(
        self,
        *,
        title: str,
        limit: int,
        include_adult: bool,
    ) -> list[Anime]:
        """Ищет тайтлы по названию.

        Args:
            title: Поисковый запрос.
            limit: Максимальное число результатов.
            include_adult: Разрешён ли взрослый контент.

        Returns:
            list[Anime]: Найденные тайтлы или пустой список при сбое.
        """
        query = search_query(include_adult)
        variables: dict[str, object] = {"search": title, "perPage": limit}
        try:
            data = await self._post_page(query, variables)
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return []

        result = []
        for item in data:
            if await is_nsfw_anilist(item) and not include_adult:
                continue
            result.append(await build_anime_from_anilist_item(item, fallback_to_anilist_id=False))
            if len(result) >= limit:
                break
        return result

    async def search_by_description(
        self,
        *,
        description: str,
        limit: int,
        include_adult: bool,
    ) -> list[Anime]:
        """Ищет тайтлы по свободному описанию.

        Args:
            description: Описание аниме на естественном языке.
            limit: Максимальное число результатов.
            include_adult: Разрешён ли взрослый контент.

        Returns:
            list[Anime]: Найденные тайтлы.

        Raises:
            AniListSearchError: Сбой запроса, после которого вызывающая
                сторона переходит к поиску по названию.
        """
        query = search_query(include_adult)
        variables: dict[str, object] = {"search": description, "perPage": limit}
        try:
            data = await self._post_page(query, variables, strict=True)
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise AniListSearchError(str(exc)) from exc

        result = []
        for item in data:
            if await is_nsfw_anilist(item) and not include_adult:
                continue
            result.append(await build_anime_from_anilist_item(item, fallback_to_anilist_id=False))
        return result

    async def get_by_anilist_id(self, anime_id: int) -> Anime | None:
        """Возвращает тайтл по идентификатору AniList.

        Args:
            anime_id: Идентификатор тайтла в AniList.

        Returns:
            Anime | None: Найденный тайтл или None при сбое.
        """
        return await self._get_by_media(
            variables={"id": anime_id},
            media_expression="Media(id: $id, type: ANIME)",
            fallback_to_anilist_id=True,
        )

    async def get_by_mal_id(self, anime_id: int) -> Anime | None:
        """Возвращает тайтл по идентификатору MyAnimeList.

        Args:
            anime_id: Идентификатор тайтла в MyAnimeList.

        Returns:
            Anime | None: Найденный тайтл или None при сбое.
        """
        return await self._get_by_media(
            variables={"idMal": anime_id},
            media_expression="Media(idMal: $idMal, type: ANIME)",
            fallback_to_anilist_id=False,
        )

    async def get_season_popular(
        self,
        *,
        year: int,
        season: str,
        limit: int,
    ) -> list[Anime]:
        """Возвращает популярные тайтлы сезона.

        Args:
            year: Год сезона.
            season: Название сезона (winter, spring, summer, fall).
            limit: Максимальное число результатов.

        Returns:
            list[Anime]: Сезонная подборка или пустой список при сбое.
        """
        anilist_season = {
            "winter": "WINTER",
            "spring": "SPRING",
            "summer": "SUMMER",
            "fall": "FALL",
        }.get(str(season).strip().lower())
        if not anilist_season:
            return []
        query = season_popular_query()
        try:
            data = await self._post_page(
                query,
                {"season": anilist_season, "year": int(year), "perPage": int(limit)},
            )
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return []

        return [
            await build_anime_from_anilist_item(item, fallback_to_anilist_id=True) for item in data
        ]

    async def _post_page(
        self,
        query: str,
        variables: dict[str, object],
        *,
        strict: bool = False,
    ) -> list[dict]:
        """Выполняет запрос страницы и возвращает список тайтлов.

        Args:
            query: GraphQL-запрос.
            variables: Переменные запроса.
            strict: Пробрасывать ли ошибку разбора вместо пустой выдачи.

        Returns:
            list[dict]: Элементы ``Page.media``.

        Raises:
            httpx.HTTPError: Сетевой сбой при ``strict``.
            KeyError: Отсутствие ожидаемого поля при ``strict``.
            TypeError: Неожиданный тип payload'а при ``strict``.
            ValueError: Некорректный JSON при ``strict``.
        """
        resp = await self.session.post(self.base_url, json={"query": query, "variables": variables})
        resp.raise_for_status()
        payload = resp.json()
        if strict:
            return list(payload["data"]["Page"]["media"] or [])
        return list(payload.get("data", {}).get("Page", {}).get("media") or [])

    async def _get_by_media(
        self,
        variables: dict[str, int],
        media_expression: str,
        fallback_to_anilist_id: bool,
    ) -> Anime | None:
        """Возвращает один тайтл по переменным GraphQL.

        Args:
            variables: Переменные запроса (``id`` или ``idMal``).
            media_expression: Выражение поля ``media``.
            fallback_to_anilist_id: Использовать ли id AniList как внешний id.

        Returns:
            Anime | None: Найденный тайтл или None при сбое.
        """
        variable_types = {"id": "Int", "idMal": "Int"}
        declarations = ", ".join(
            f"${name}: {variable_type}"
            for name, variable_type in variable_types.items()
            if name in variables
        )
        query = media_query(declarations, media_expression)
        try:
            resp = await self.session.post(
                self.base_url,
                json={"query": query, "variables": variables},
            )
            resp.raise_for_status()
            item = resp.json().get("data", {}).get("media")
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return None
        if not item:
            return None
        return await build_anime_from_anilist_item(
            item,
            fallback_to_anilist_id=fallback_to_anilist_id,
        )
