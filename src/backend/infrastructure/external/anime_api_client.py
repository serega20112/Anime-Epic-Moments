"""Orchestrating facade over the Jikan and AniList anime providers."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from backend.domain.entities.anime.anime import Anime
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.external.anilist_client import (
    AniListAnimeClient,
    AniListSearchError,
)
from backend.infrastructure.external.jikan_client import JikanAnimeClient
from backend.infrastructure.external.mapping.anime import passes_filters, sanitize_query

_CACHE_MISS = object()


class AnimeApiClient:
    """Fetch anime data from the Jikan API and AniList GraphQL.

    Owns the shared HTTP session, the cache store and the fallback/race
    orchestration. Provider-specific network calls are delegated to the
    :class:`JikanAnimeClient` and :class:`AniListAnimeClient` collaborators,
    while payload mapping happens in the pure mapping helpers on the layer
    boundary.
    """

    def __init__(self, store: KeyValueStore | None = None):
        """Initialize the client.

        Args:
            store: Optional cache store.
        """
        self.store = store or KeyValueStore(redis_url=None, namespace="anime_api")
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=3.0, read=6.0, write=3.0, pool=3.0),
            trust_env=False,
        )
        self.jikan = JikanAnimeClient(self.session)
        self.anilist = AniListAnimeClient(self.session)

    @property
    def jikan_base(self) -> str:
        """Jikan API base URL (used for introspection and tests)."""
        return self.jikan.base_url

    @property
    def anilist_base(self) -> str:
        """AniList GraphQL base URL (used for introspection and tests)."""
        return self.anilist.base_url

    @property
    def genre_id_map(self) -> dict[str, int]:
        """Jikan genre id map (kept for backward compatibility)."""
        return self.jikan.genre_id_map

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self.session.aclose()

    async def search_by_title(
        self, title: str, limit: int = 10, include_adult: bool = False
    ) -> list[Anime]:
        """Search anime by title, falling back to AniList when Jikan yields nothing.

        Args:
            title: Search query.
            limit: Maximum number of results.
            include_adult: Whether adult content is allowed.

        Returns:
            list[Anime]: Matching anime.
        """
        sanitized_title = await sanitize_query(title)
        if not sanitized_title:
            return []
        cache_key = await self._cache_key(
            "search_by_title_v2",
            sanitized_title.lower(),
            int(limit),
            int(bool(include_adult)),
        )
        cached = await self._get_cached(cache_key)
        if cached is not _CACHE_MISS:
            return list(cached)
        result = await self.jikan.search_by_title(
            sanitized_title,
            limit=limit,
            include_adult=include_adult,
        )
        if not result:
            result = await self.anilist.search_by_title(
                title=sanitized_title,
                limit=limit,
                include_adult=include_adult,
            )
            ttl_seconds = 300 if result else 60
            return list(await self._set_cached(cache_key, result, ttl_seconds=ttl_seconds))
        return list(await self._set_cached(cache_key, result, ttl_seconds=300))

    async def get_season_popular(self, year: int, season: str, limit: int = 10) -> list[Anime]:
        """Fetch popular anime of a season, falling back to AniList.

        Args:
            year: Season year.
            season: Season name (winter, spring, summer, fall).
            limit: Maximum number of results.

        Returns:
            list[Anime]: Popular anime.
        """
        cache_key = await self._cache_key(
            "season_popular",
            int(year),
            str(season).strip().lower(),
            int(limit),
        )
        cached = await self._get_cached(cache_key)
        if cached is not _CACHE_MISS:
            return list(cached)
        result = await self.jikan.get_season_popular(year, season, limit)
        if not result:
            result = await self.anilist.get_season_popular(year=year, season=season, limit=limit)
            ttl_seconds = 900 if result else 60
            return list(await self._set_cached(cache_key, result, ttl_seconds=ttl_seconds))
        return list(await self._set_cached(cache_key, result, ttl_seconds=900))

    async def search_by_description(
        self,
        description: str,
        year_from: int | None = None,
        year_to: int | None = None,
        min_rating: int | None = None,
        include_adult: bool = False,
        limit: int = 10,
    ) -> list[Anime]:
        """Search anime by free-form description through AniList GraphQL.

        Falls back to a title search when AniList is unreachable.

        Args:
            description: Natural language anime description.
            year_from: Optional minimum season year.
            year_to: Optional maximum season year.
            min_rating: Optional minimum normalized rating.
            include_adult: Whether adult content is allowed.
            limit: Maximum number of results.

        Returns:
            list[Anime]: Matching anime.
        """
        sanitized_description = await sanitize_query(description)
        if not sanitized_description:
            return []
        cache_key = await self._cache_key(
            "search_by_description",
            sanitized_description.lower(),
            year_from if year_from is not None else "",
            year_to if year_to is not None else "",
            min_rating if min_rating is not None else "",
            int(bool(include_adult)),
            int(limit),
        )
        cached = await self._get_cached(cache_key)
        if cached is not _CACHE_MISS:
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
            return list(await self._set_cached(cache_key, fallback, ttl_seconds=300))

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
        return list(await self._set_cached(cache_key, result, ttl_seconds=300))

    async def get_by_id(self, anime_id: int) -> Anime | None:
        """Fetch anime by id, trying Jikan and AniList concurrently.

        Whenever a provider hangs (e.g. Jikan timing out), the other provider
        (AniList) can satisfy the request immediately instead of blocking on
        the slow/failing upstream.

        Args:
            anime_id: Anime identifier.

        Returns:
            Anime | None: The anime or None when unavailable.
        """
        anime_id = int(anime_id)
        cache_key = await self._cache_key("anime", anime_id)
        cached = await self._get_cached(cache_key)
        if cached is not _CACHE_MISS:
            return cached
        result = await self._first_truthy(
            self.jikan.get_by_id(anime_id),
            self._get_by_anilist_id(anime_id),
            self._get_by_anilist_mal_id(anime_id),
        )
        return await self._set_cached(cache_key, result, ttl_seconds=1800)

    async def _get_by_anilist_id(self, anime_id: int) -> Anime | None:
        """Fetch anime by AniList id as a fallback.

        Args:
            anime_id: AniList anime identifier.

        Returns:
            Anime | None: The anime or None when unavailable.
        """
        return await self.anilist.get_by_anilist_id(anime_id)

    async def _get_by_anilist_mal_id(self, anime_id: int) -> Anime | None:
        """Fetch anime by AniList MAL (idMal) as an additional fallback.

        The same ``anime_id`` can be either an AniList id or a MyAnimeList
        (MAL) id, depending on which of the racing catalog providers produced
        the tile (Jikan yields MAL ids, AniList yields ``idMal`` values when
        present). Resolving the id as a MAL id via AniList ``idMal`` covers the
        case where Jikan (the primary MAL source) is unavailable or the id was
        never an AniList id.

        Args:
            anime_id: MyAnimeList anime identifier.

        Returns:
            Anime | None: The anime or None when unavailable.
        """
        return await self.anilist.get_by_mal_id(anime_id)

    async def get_top_anime(self, limit: int = 25) -> list[Anime]:
        """Fetch popular anime through the Jikan top endpoint.

        Args:
            limit: Maximum number of results.

        Returns:
            list[Anime]: Popular anime.
        """
        cache_key = await self._cache_key("top", int(limit))
        cached = await self._get_cached(cache_key)
        if cached is not _CACHE_MISS:
            return list(cached)
        result = await self.jikan.get_top_anime(limit)
        return list(await self._set_cached(cache_key, result, ttl_seconds=900))

    async def filter_catalog(
        self,
        *,
        genre: str = "",
        media_type: str = "",
        status: str = "",
        year_from: int | None = None,
        year_to: int | None = None,
        min_score: float | None = None,
        sort: str = "rating",
        order: str = "desc",
        limit: int = 30,
    ) -> list[Anime]:
        """Browse anime with Anixart-like filters, racing Jikan and AniList.

        Args:
            genre: Comma-separated genre/tag names or empty string for all.
            media_type: Format filter (tv, movie, ova, ona, special). Empty means all.
            status: Status filter (airing, complete, upcoming). Empty means all.
            year_from: Optional lower bound release year.
            year_to: Optional upper bound release year.
            min_score: Optional minimum normalized rating (0-10).
            sort: Sorting strategy (rating, popularity, newest, title).
            order: Sorting direction (asc, desc).
            limit: Maximum number of results to return.

        Returns:
            list[Anime]: Filtered and sorted anime.
        """
        sort_key = sort
        valid_sorts = {"rating", "popularity", "newest", "title"}
        if sort_key not in valid_sorts:
            sort_key = "rating"
        order_key = "asc" if str(order).strip().lower() == "asc" else "desc"
        cache_key = await self._cache_key(
            "filter_catalog_v1",
            str(genre).strip().lower(),
            str(media_type).strip().lower(),
            str(status).strip().lower(),
            year_from if year_from is not None else "",
            year_to if year_to is not None else "",
            min_score if min_score is not None else "",
            sort_key,
            order_key,
            int(limit),
        )
        cached = await self._get_cached(cache_key)
        if cached is not _CACHE_MISS:
            return list(cached)

        result = await self._first_truthy(
            self.jikan.filter_catalog(
                genre=genre,
                media_type=media_type,
                status=status,
                year_from=year_from,
                year_to=year_to,
                min_score=min_score,
                sort=sort_key,
                order=order_key,
                limit=limit,
            ),
            self.anilist.filter_catalog(
                genre=genre,
                media_type=media_type,
                status=status,
                year_from=year_from,
                year_to=year_to,
                min_score=min_score,
                sort=sort_key,
                order=order_key,
                limit=limit,
            ),
        )
        ttl_seconds = 600 if result else 60
        return list(await self._set_cached(cache_key, result or [], ttl_seconds=ttl_seconds))

    async def _first_truthy(self, *awaitables) -> Any:
        """Await several coroutines and return the first truthy result.

        Cancels the remaining pending tasks as soon as one yields a truthy
        result, so a hanging provider does not delay the response.

        Args:
            *awaitables: Coroutines to race.

        Returns:
            The first truthy value, or None when all yield falsy results.
        """
        tasks = [asyncio.ensure_future(item) for item in awaitables]
        pending = list(tasks)
        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                try:
                    value = task.result()
                except Exception:
                    value = None
                if value:
                    for other in pending:
                        other.cancel()
                    return value
        return None

    async def _cache_key(self, *parts: object) -> str:
        """Build a colon-separated cache key.

        Args:
            parts: Key parts.

        Returns:
            str: Joined cache key.
        """
        return ":".join(str(part) for part in parts)

    async def _get_cached(self, key: str):
        """Read a value from the cache store.

        Args:
            key: Cache key.

        Returns:
            object: Cached value or _CACHE_MISS.
        """
        if self.store is None:
            return _CACHE_MISS
        try:
            if not await self.store.contains(key):
                return _CACHE_MISS
            return await self.store.get(key)
        except Exception:
            return _CACHE_MISS

    async def _set_cached(self, key: str, value, ttl_seconds: int):
        """Store a value in the cache store.

        Args:
            key: Cache key.
            value: Value to store.
            ttl_seconds: TTL in seconds.

        Returns:
            object: The stored value.
        """
        if self.store is None:
            return value
        try:
            await self.store.set(key, value, ttl_seconds=ttl_seconds)
        except Exception:
            pass
        return value
