from typing import Any

import httpx

from backend.domain.anime.entity import Anime
from backend.infrastructure.cache.key_value_store import KeyValueStore

_CACHE_MISS = object()


class AnimeApiClient:
    """Fetch anime data from the Jikan API and AniList GraphQL.

    Provides domain Anime objects with in-memory or Redis backed caching.
    """

    def __init__(self, store: KeyValueStore | None = None):
        """Initialize the client.

        Args:
            store: Optional cache store.
        """
        self.jikan_base = "https://api.jikan.moe/v4"
        self.anilist_base = "https://graphql.anilist.co"
        self.session = httpx.AsyncClient(timeout=20.0, trust_env=False)
        self.store = store or KeyValueStore(redis_url=None, namespace="anime_api")

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self.session.aclose()

    async def search_by_title(
        self, title: str, limit: int = 10, include_adult: bool = False
    ) -> list[Anime]:
        """Search anime by title through Jikan.

        Args:
            title: Search query.
            limit: Maximum number of results.
            include_adult: Whether adult content is allowed.

        Returns:
            list[Anime]: Matching anime.
        """
        sanitized_title = self._sanitize_query(title)
        if not sanitized_title:
            return []
        cache_key = self._cache_key(
            "search_by_title_v2",
            sanitized_title.lower(),
            int(limit),
            int(bool(include_adult)),
        )
        cached = await self._get_cached(cache_key)
        if cached is not _CACHE_MISS:
            return list(cached)
        url = f"{self.jikan_base}/anime"
        params = {"q": sanitized_title, "limit": limit}
        try:
            resp = await self.session.get(url, params=params)
            resp.raise_for_status()
            data = resp.json().get("data", [])
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            fallback = await self._search_by_title_via_anilist(
                title=sanitized_title,
                limit=limit,
                include_adult=include_adult,
            )
            ttl_seconds = 300 if fallback else 60
            return list(await self._set_cached(cache_key, fallback, ttl_seconds=ttl_seconds))

        result = []
        for item in data:
            if self._is_nsfw_jikan(item) and not include_adult:
                continue
            result.append(self._build_anime_from_jikan_item(item))
        if not result:
            fallback = await self._search_by_title_via_anilist(
                title=sanitized_title,
                limit=limit,
                include_adult=include_adult,
            )
            ttl_seconds = 300 if fallback else 60
            return list(await self._set_cached(cache_key, fallback, ttl_seconds=ttl_seconds))
        return list(await self._set_cached(cache_key, result, ttl_seconds=300))

    async def get_season_popular(self, year: int, season: str, limit: int = 10) -> list[Anime]:
        """Fetch popular anime of a season through Jikan.

        Args:
            year: Season year.
            season: Season name (winter, spring, summer, fall).
            limit: Maximum number of results.

        Returns:
            list[Anime]: Popular anime.
        """
        cache_key = self._cache_key(
            "season_popular",
            int(year),
            str(season).strip().lower(),
            int(limit),
        )
        cached = await self._get_cached(cache_key)
        if cached is not _CACHE_MISS:
            return list(cached)
        url = f"{self.jikan_base}/seasons/{year}/{season}"
        result = []
        try:
            resp = await self.session.get(url)
            resp.raise_for_status()
            data = resp.json().get("data", [])[:limit]
            for item in data:
                result.append(self._build_anime_from_jikan_item(item))
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            result = []
        if not result:
            result = await self._get_season_popular_via_anilist(
                year=year, season=season, limit=limit
            )
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
        query = """
        query ($search: String, $perPage: Int, $isAdult: Boolean) {
          Page(perPage: $perPage) {
            media(search: $search, type: ANIME, isAdult: $isAdult) {
              id
              idMal
              episodes
              title { romaji english native }
              description
              genres
              isAdult
              seasonYear
              averageScore
              coverImage { large }
            }
          }
        }
        """
        sanitized_description = self._sanitize_query(description)
        if not sanitized_description:
            return []
        cache_key = self._cache_key(
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
        variables: dict[str, object] = {
            "search": sanitized_description,
            "perPage": limit,
            "isAdult": None if include_adult else False,
        }
        try:
            resp = await self.session.post(
                self.anilist_base,
                json={"query": query, "variables": variables},
            )
            resp.raise_for_status()
            data = resp.json()["data"]["Page"]["media"]
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            fallback = await self.search_by_title(
                title=sanitized_description, limit=limit, include_adult=include_adult
            )
            return list(await self._set_cached(cache_key, fallback, ttl_seconds=300))

        result = []
        for item in data:
            if self._is_nsfw_anilist(item) and not include_adult:
                continue
            season_year = item.get("seasonYear")
            average_score = item.get("averageScore")
            normalized_score = (
                (average_score / 10) if isinstance(average_score, (int, float)) else None
            )
            if not self._passes_filters(
                season_year=season_year,
                normalized_score=normalized_score,
                year_from=year_from,
                year_to=year_to,
                min_rating=min_rating,
            ):
                continue
            result.append(
                self._build_anime_from_anilist_item(
                    item,
                    fallback_to_anilist_id=False,
                )
            )
            if len(result) >= limit:
                break
        return list(await self._set_cached(cache_key, result, ttl_seconds=300))

    async def get_by_id(self, anime_id: int) -> Anime | None:
        """Fetch anime by id with Jikan priority and AniList fallback.

        Args:
            anime_id: Anime identifier.

        Returns:
            Anime | None: The anime or None when unavailable.
        """
        anime_id = int(anime_id)
        cache_key = self._cache_key("anime", anime_id)
        cached = await self._get_cached(cache_key)
        if cached is not _CACHE_MISS:
            return cached
        url = f"{self.jikan_base}/anime/{anime_id}"
        try:
            resp = await self.session.get(url)
            resp.raise_for_status()
            item = resp.json().get("data")
            if not item:
                return await self._set_cached(
                    cache_key, await self._get_by_anilist_id(anime_id), ttl_seconds=1800
                )
        except httpx.HTTPStatusError as error:
            status_code = error.response.status_code if error.response else None
            if status_code == 404:
                return await self._set_cached(
                    cache_key, await self._get_by_anilist_id(anime_id), ttl_seconds=1800
                )
            anime = await self._get_by_mal_id_via_anilist(anime_id)
            fallback = anime or await self._get_by_anilist_id(anime_id)
            return await self._set_cached(cache_key, fallback, ttl_seconds=1800)
        except (httpx.RequestError, ValueError, KeyError, TypeError):
            anime = await self._get_by_mal_id_via_anilist(anime_id)
            fallback = anime or await self._get_by_anilist_id(anime_id)
            return await self._set_cached(cache_key, fallback, ttl_seconds=1800)

        return await self._set_cached(
            cache_key,
            self._build_anime_from_jikan_item(item),
            ttl_seconds=1800,
        )

    async def _get_by_mal_id_via_anilist(self, anime_id: int) -> Anime | None:
        """Fetch anime by MAL id via AniList.

        Args:
            anime_id: MAL anime identifier.

        Returns:
            Anime | None: The anime or None when unavailable.
        """
        return await self._get_by_anilist_media(
            variables={"idMal": anime_id},
            media_expression="Media(idMal: $idMal, type: ANIME)",
            fallback_to_anilist_id=False,
        )

    async def get_top_anime(self, limit: int = 25) -> list[Anime]:
        """Fetch popular anime through the Jikan top endpoint.

        Args:
            limit: Maximum number of results.

        Returns:
            list[Anime]: Popular anime.
        """
        cache_key = self._cache_key("top", int(limit))
        cached = await self._get_cached(cache_key)
        if cached is not _CACHE_MISS:
            return list(cached)
        url = f"{self.jikan_base}/top/anime"
        try:
            resp = await self.session.get(url, params={"limit": limit})
            resp.raise_for_status()
            data = resp.json().get("data", [])
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return list(await self._set_cached(cache_key, [], ttl_seconds=900))

        result = []
        for item in data:
            result.append(self._build_anime_from_jikan_item(item))
        return list(await self._set_cached(cache_key, result, ttl_seconds=900))

    async def _get_by_anilist_id(self, anime_id: int) -> Anime | None:
        """Fetch anime by AniList id as a fallback.

        Args:
            anime_id: AniList anime identifier.

        Returns:
            Anime | None: The anime or None when unavailable.
        """
        return await self._get_by_anilist_media(
            variables={"id": anime_id},
            media_expression="Media(id: $id, type: ANIME)",
            fallback_to_anilist_id=True,
        )

    async def _get_by_anilist_media(
        self,
        variables: dict[str, int],
        media_expression: str,
        fallback_to_anilist_id: bool,
    ) -> Anime | None:
        """Fetch a single anime by AniList GraphQL variables.

        Args:
            variables: GraphQL variables.
            media_expression: AniList media expression.
            fallback_to_anilist_id: Whether to use the AniList id as external id.

        Returns:
            Anime | None: The anime or None when unavailable.
        """
        query = """
        query ($id: Int, $idMal: Int) {
          media: PLACEHOLDER_MEDIA_EXPRESSION {
            id
            idMal
            episodes
            title { romaji english native }
            description
            genres
            isAdult
            seasonYear
            averageScore
            coverImage { large }
          }
        }
        """.replace("PLACEHOLDER_MEDIA_EXPRESSION", media_expression)
        try:
            resp = await self.session.post(
                self.anilist_base,
                json={"query": query, "variables": variables},
            )
            resp.raise_for_status()
            item = resp.json().get("data", {}).get("media")
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return None
        if not item:
            return None
        return self._build_anime_from_anilist_item(
            item,
            fallback_to_anilist_id=fallback_to_anilist_id,
        )

    async def _get_season_popular_via_anilist(
        self,
        *,
        year: int,
        season: str,
        limit: int,
    ) -> list[Anime]:
        """Fetch season popular anime via AniList as a fallback.

        Args:
            year: Season year.
            season: Season name.
            limit: Maximum number of results.

        Returns:
            list[Anime]: Popular anime.
        """
        anilist_season = {
            "winter": "WINTER",
            "spring": "SPRING",
            "summer": "SUMMER",
            "fall": "FALL",
        }.get(str(season).strip().lower())
        if not anilist_season:
            return []
        query = """
        query ($season: MediaSeason, $year: Int, $perPage: Int) {
          Page(perPage: $perPage) {
            media(
              season: $season
              seasonYear: $year
              type: ANIME
              isAdult: false
              sort: SCORE_DESC
            ) {
              id
              title { romaji english native }
              seasonYear
              coverImage { large }
            }
          }
        }
        """
        try:
            resp = await self.session.post(
                self.anilist_base,
                json={
                    "query": query,
                    "variables": {
                        "season": anilist_season,
                        "year": int(year),
                        "perPage": int(limit),
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json().get("data", {}).get("Page", {}).get("media", [])
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return []

        result = []
        for item in data:
            result.append(
                self._build_anime_from_anilist_item(
                    item,
                    fallback_to_anilist_id=True,
                )
            )
        return result

    async def _search_by_title_via_anilist(
        self,
        *,
        title: str,
        limit: int,
        include_adult: bool,
    ) -> list[Anime]:
        """Search anime by title via AniList as a fallback.

        Args:
            title: Search query.
            limit: Maximum number of results.
            include_adult: Whether adult content is allowed.

        Returns:
            list[Anime]: Matching anime.
        """
        query = """
        query ($search: String, $perPage: Int, $isAdult: Boolean) {
          Page(perPage: $perPage) {
            media(search: $search, type: ANIME, isAdult: $isAdult) {
              id
              idMal
              episodes
              title { romaji english native }
              description
              genres
              isAdult
              seasonYear
              averageScore
              coverImage { large }
            }
          }
        }
        """
        variables: dict[str, object] = {
            "search": title,
            "perPage": limit,
            "isAdult": None if include_adult else False,
        }
        try:
            resp = await self.session.post(
                self.anilist_base,
                json={"query": query, "variables": variables},
            )
            resp.raise_for_status()
            data = resp.json().get("data", {}).get("Page", {}).get("media", [])
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return []

        result = []
        for item in data:
            if self._is_nsfw_anilist(item) and not include_adult:
                continue
            result.append(
                self._build_anime_from_anilist_item(
                    item,
                    fallback_to_anilist_id=False,
                )
            )
            if len(result) >= limit:
                break
        return result

    def _passes_filters(
        self,
        season_year: int | None,
        normalized_score: float | None,
        year_from: int | None,
        year_to: int | None,
        min_rating: int | None,
    ) -> bool:
        """Check whether an anime passes year and rating filters.

        Args:
            season_year: Anime release season year.
            normalized_score: Normalized average score.
            year_from: Minimum season year or None.
            year_to: Maximum season year or None.
            min_rating: Minimum normalized rating or None.

        Returns:
            bool: True when the anime passes all filters.
        """
        if year_from is not None and (season_year is None or season_year < year_from):
            return False
        if year_to is not None and (season_year is None or season_year > year_to):
            return False
        if min_rating is not None and (normalized_score is None or normalized_score < min_rating):
            return False
        return True

    def _sanitize_query(self, query: str | None) -> str:
        """Strip control and redundant characters from a search query.

        Args:
            query: Raw search query.

        Returns:
            str: Sanitized query.
        """
        if not query:
            return ""
        normalized = str(query).replace("\x00", " ").replace("\u0000", " ")
        normalized = " ".join(normalized.split())
        return normalized.strip()

    def _build_anime_from_jikan_item(self, item: dict[str, Any]) -> Anime:
        """Build a domain Anime from a Jikan item dict.

        Args:
            item: Jikan API item.

        Returns:
            Anime: Domain anime.
        """
        return Anime(
            external_id=self._normalize_numeric_id(item.get("mal_id")),
            title=str(item.get("title") or "").strip(),
            description=item.get("synopsis"),
            genres=[
                str(genre.get("name") or "").strip()
                for genre in item.get("genres", [])
                if isinstance(genre, dict) and genre.get("name")
            ],
            year=item.get("year"),
            rating=item.get("score"),
            cover_url=item.get("images", {}).get("jpg", {}).get("image_url"),
            episode_count=self._normalize_episode_count(item.get("episodes")),
        )

    def _build_anime_from_anilist_item(
        self,
        item: dict[str, Any],
        fallback_to_anilist_id: bool,
    ) -> Anime:
        """Build a domain Anime from an AniList item dict.

        Args:
            item: AniList API item.
            fallback_to_anilist_id: Whether to prefer the AniList id.

        Returns:
            Anime: Domain anime.
        """
        title_data = item.get("title", {}) or {}
        average_score = item.get("averageScore")
        normalized_score = (average_score / 10) if isinstance(average_score, (int, float)) else None
        mal_id = self._normalize_numeric_id(item.get("idMal"))
        anilist_id = self._normalize_numeric_id(item.get("id"))
        external_id = mal_id or (anilist_id if fallback_to_anilist_id else "")

        return Anime(
            external_id=external_id,
            title=self._pick_anilist_title(title_data),
            description=item.get("description"),
            genres=[str(genre).strip() for genre in (item.get("genres", []) or []) if genre],
            year=item.get("seasonYear"),
            rating=normalized_score,
            cover_url=item.get("coverImage", {}).get("large"),
            episode_count=self._normalize_episode_count(item.get("episodes")),
        )

    def _pick_anilist_title(self, title_data: dict[str, Any]) -> str:
        """Pick the best available AniList title.

        Args:
            title_data: AniList title mapping.

        Returns:
            str: Chosen title.
        """
        for key in ("romaji", "english", "native"):
            value = str(title_data.get(key) or "").strip()
            if value:
                return value
        return "Unknown anime"

    def _normalize_numeric_id(self, value: Any) -> str:
        """Normalize a numeric id to a positive string.

        Args:
            value: Raw id value.

        Returns:
            str: Normalized id or empty string.
        """
        if isinstance(value, bool) or value is None:
            return ""
        try:
            numeric_value = int(value)
        except (TypeError, ValueError):
            return ""
        return str(numeric_value) if numeric_value > 0 else ""

    def _normalize_episode_count(self, value: Any) -> int | None:
        """Normalize an episode count to a positive integer.

        Args:
            value: Raw episode count.

        Returns:
            int | None: Normalized count or None.
        """
        if isinstance(value, bool) or value is None:
            return None
        try:
            numeric_value = int(value)
        except (TypeError, ValueError):
            return None
        return numeric_value if numeric_value > 0 else None

    def _is_nsfw_jikan(self, item: dict) -> bool:
        """Detect NSFW content from a Jikan rating string.

        Args:
            item: Jikan API item.

        Returns:
            bool: True when the item is NSFW.
        """
        rating_text = str(item.get("rating") or "").lower()
        nsfw_markers = ("hentai", "explicit", "porn", "rx")
        return any(marker in rating_text for marker in nsfw_markers)

    def _is_nsfw_anilist(self, item: dict) -> bool:
        """Detect NSFW content from AniList metadata.

        Args:
            item: AniList API item.

        Returns:
            bool: True when the item is NSFW.
        """
        if bool(item.get("isAdult")):
            return True
        genres = item.get("genres", []) or []
        return any(str(genre).strip().lower() == "hentai" for genre in genres)

    def _cache_key(self, *parts: object) -> str:
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
        if not await self.store.contains(key):
            return _CACHE_MISS
        return await self.store.get(key)

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
        await self.store.set(key, value, ttl_seconds=ttl_seconds)
        return value
