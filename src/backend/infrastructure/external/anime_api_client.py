import asyncio
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
        self.genre_id_map = {
            "Action": 1, "Adventure": 2, "Cars": 3, "Comedy": 4,
            "Dementia": 5, "Demons": 6, "Mystery": 7, "Drama": 8,
            "Ecchi": 9, "Fantasy": 10, "Gender Bender": 11, "Harem": 35,
            "Historical": 13, "Horror": 14, "Kids": 15, "Magic": 16,
            "Martial Arts": 17, "Mecha": 18, "Music": 19,
            "Parody": 20, "Psychological": 40, "Romance": 22, "Samurai": 21,
            "School": 23, "Sci-Fi": 24, "Seinen": 42, "Shoujo": 25,
            "Shounen": 27, "Slice of Life": 36, "Space": 29, "Sports": 30,
            "Super Power": 31, "Supernatural": 37, "Thriller": 41,
            "Vampire": 32,
        }
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=3.0, read=6.0, write=3.0, pool=3.0),
            trust_env=False,
        )
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
        cache_key = self._cache_key("anime", anime_id)
        cached = await self._get_cached(cache_key)
        if cached is not _CACHE_MISS:
            return cached
        result = await self._first_truthy(
            self._get_by_jikan(anime_id),
            self._get_by_anilist_id(anime_id),
        )
        return await self._set_cached(cache_key, result, ttl_seconds=1800)

    async def _get_by_jikan(self, anime_id: int) -> Anime | None:
        """Fetch anime by id from the Jikan API."""
        url = f"{self.jikan_base}/anime/{anime_id}"
        try:
            resp = await self.session.get(url)
            resp.raise_for_status()
            item = resp.json().get("data")
            if not item:
                return None
            return self._build_anime_from_jikan_item(item)
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return None

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
        """Browse anime with Anixart-like filters.

        Args:
            genre: Selected genre name or empty string for all.
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
        cache_key = self._cache_key(
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
            self._filter_catalog_via_jikan(
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
            self._filter_catalog_via_anilist(
                genre=genre,
                media_type=media_type,
                status=status,
                year_from=year_from,
                year_to=year_to,
                min_score=min_score,
                sort=sort_key,
                limit=limit,
            ),
        )
        ttl_seconds = 600 if result else 60
        return list(await self._set_cached(cache_key, result or [], ttl_seconds=ttl_seconds))

    async def _filter_catalog_via_jikan(
        self,
        *,
        genre: str,
        media_type: str,
        status: str,
        year_from: int | None,
        year_to: int | None,
        min_score: float | None,
        sort: str,
        order: str,
        limit: int,
    ) -> list[Anime]:
        """Filter and sort anime through the Jikan /anime endpoint.

        Args:
            genre: Selected genre name.
            media_type: Format filter value.
            status: Status filter value.
            year_from: Optional lower bound release year.
            year_to: Optional upper bound release year.
            min_score: Optional minimum normalized rating.
            sort: Normalized sort key.
            order: Sorting direction.
            limit: Maximum number of results to return.

        Returns:
            list[Anime]: Filtered and sorted anime.
        """
        params: dict[str, object] = {"limit": limit, "sfw": "true"}
        genre_id = self.genre_id_map.get(str(genre).strip().title())
        if genre_id:
            params["genres"] = genre_id
        normalized_type = str(media_type).strip().lower()
        if normalized_type in {"tv", "movie", "ova", "ona", "special", "music"}:
            params["type"] = normalized_type
        normalized_status = str(status).strip().lower()
        if normalized_status in {"airing", "complete", "upcoming"}:
            params["status"] = normalized_status
        if isinstance(year_from, int):
            params["start_date"] = f"{year_from}-01-01"
        if isinstance(year_to, int):
            params["end_date"] = f"{year_to}-12-31"
        if isinstance(min_score, (int, float)) and 0 <= float(min_score) <= 10:
            params["min_score"] = float(min_score)
        order_by_map = {
            "rating": "score",
            "popularity": "members",
            "newest": "start_date",
            "title": "title",
        }
        params["order_by"] = order_by_map.get(sort, "score")
        params["sort"] = order
        try:
            resp = await self.session.get(f"{self.jikan_base}/anime", params=params)
            resp.raise_for_status()
            data = resp.json().get("data", [])
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return []

        result = []
        for item in data:
            if self._is_nsfw_jikan(item):
                continue
            result.append(self._build_anime_from_jikan_item(item))
        return result

    async def _filter_catalog_via_anilist(
        self,
        *,
        genre: str,
        media_type: str,
        status: str,
        year_from: int | None,
        year_to: int | None,
        min_score: float | None,
        sort: str,
        limit: int,
    ) -> list[Anime]:
        """Filter and sort anime via an AniList GraphQL fallback.

        Args:
            genre: Selected genre name.
            media_type: Format filter value.
            status: Status filter value.
            year_from: Optional lower bound release year.
            year_to: Optional upper bound release year.
            min_score: Optional minimum normalized rating.
            sort: Normalized sort key.
            limit: Maximum number of results to return.

        Returns:
            list[Anime]: Filtered and sorted anime.
        """
        format_map = {"tv": "TV", "movie": "MOVIE", "ova": "OVA", "ona": "ONA", "special": "SPECIAL"}
        status_map = {"airing": "RELEASING", "complete": "FINISHED", "upcoming": "NOT_YET_RELEASED"}
        sort_map = {
            "rating": "SCORE_DESC",
            "popularity": "POPULARITY_DESC",
            "newest": "START_DATE_DESC",
            "title": "TITLE_ROMAJI",
        }

        def parse_anilist_media(payload_data: list) -> list[Anime]:
            result = []
            for item in payload_data:
                if self._is_nsfw_anilist(item):
                    continue
                result.append(
                    self._build_anime_from_anilist_item(
                        item,
                        fallback_to_anilist_id=True,
                    )
                )
            return result

        # Собираем media-аргументы и переменные только для заданных фильтров,
        # чтобы не передавать AniList значения типа genre_in: [null] (это 400).
        args = ["type: ANIME", "isAdult: false", "sort: PLACEHOLDER_SORT"]
        declarations = ["$perPage: Int"]
        variables: dict[str, object] = {"perPage": int(limit)}

        if genre:
            args.append("genre_in: [$genre]")
            declarations.append("$genre: String")
            variables["genre"] = str(genre).strip()

        normalized_type = str(media_type).strip().lower()
        if normalized_type in format_map:
            args.append("format: $format")
            declarations.append("$format: MediaFormat")
            variables["format"] = format_map[normalized_type]

        normalized_status = str(status).strip().lower()
        if normalized_status in status_map:
            args.append("status: $status")
            declarations.append("$status: MediaStatus")
            variables["status"] = status_map[normalized_status]

        if isinstance(year_from, int):
            args.append("seasonYear_greater: $yearGreater")
            declarations.append("$yearGreater: FuzzyDateInt")
            variables["yearGreater"] = year_from - 1
        if isinstance(year_to, int):
            args.append("seasonYear_lesser: $yearLess")
            declarations.append("$yearLess: FuzzyDateInt")
            variables["yearLess"] = year_to + 1
        if isinstance(min_score, (int, float)) and 0 <= float(min_score) <= 10:
            args.append("averageScore_greater: $minScore")
            declarations.append("$minScore: Int")
            variables["minScore"] = int(float(min_score) * 10)

        query = (
            """
            query (%s) {
              Page(perPage: $perPage) {
                media(%s) {
                  id
                  idMal
                  episodes
                  title { romaji english native }
                  description
                  genres
                  seasonYear
                  averageScore
                  coverImage { large }
                }
              }
            }
            """
            % (", ".join(declarations), " ".join(args))
        ).replace("PLACEHOLDER_SORT", sort_map.get(sort, "SCORE_DESC"))
        try:
            resp = await self.session.post(
                self.anilist_base,
                json={"query": query, "variables": variables},
            )
            resp.raise_for_status()
            data = resp.json().get("data", {}).get("Page", {}).get("media", [])
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return []
        return parse_anilist_media(data)

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
        variable_types = {"id": "Int", "idMal": "Int"}
        declarations = ", ".join(
            f"${name}: {variable_type}"
            for name, variable_type in variable_types.items()
            if name in variables
        )
        query = f"""
        query ({declarations}) {{
          media: {media_expression} {{
            id
            idMal
            episodes
            title {{ romaji english native }}
            description
            genres
            isAdult
            seasonYear
            averageScore
            coverImage {{ large }}
          }}
        }}
        """
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
