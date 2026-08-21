"""AniList GraphQL anime client."""

from __future__ import annotations

import httpx

from backend.domain.entities.anime.anime import Anime
from backend.infrastructure.external.errors import ExternalServiceError
from backend.infrastructure.external.mapping.anime import (
    build_anime_from_anilist_item,
    is_nsfw_anilist,
)

ANILIST_BASE_URL = "https://graphql.anilist.co"


class AniListSearchError(ExternalServiceError):
    """Raised when an AniList description search fails on the network layer.

    Unlike the other AniList methods, which degrade to empty results because
    they are used as racing or fallback sources, the description search signals
    failures so the orchestrator can fall back to a title search.
    """

    service_name = "anilist"


class AniListAnimeClient:
    """Fetch anime data from the AniList GraphQL API.

    Only performs network I/O against AniList and delegates payload mapping to
    the pure mapping helpers. Most methods degrade to empty results on
    failures; only :meth:`search_by_description` raises
    :class:`AniListSearchError`.
    """

    def __init__(self, session: httpx.AsyncClient, base_url: str = ANILIST_BASE_URL):
        """Initialize the client.

        Args:
            session: Shared HTTP client owned by the orchestrating facade.
            base_url: AniList GraphQL base URL.
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
        """Search anime by title.

        Args:
            title: Search query.
            limit: Maximum number of results.
            include_adult: Whether adult content is allowed.

        Returns:
            list[Anime]: Matching anime, or an empty list on failure.
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
                self.base_url,
                json={"query": query, "variables": variables},
            )
            resp.raise_for_status()
            data = resp.json().get("data", {}).get("Page", {}).get("media", [])
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
        """Search anime by free-form description.

        Args:
            description: Natural language anime description.
            limit: Maximum number of results.
            include_adult: Whether adult content is allowed.

        Returns:
            list[Anime]: Matching anime.

        Raises:
            AniListSearchError: When the AniList request fails so the caller can
                fall back to a title search.
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
            "search": description,
            "perPage": limit,
            "isAdult": None if include_adult else False,
        }
        try:
            resp = await self.session.post(
                self.base_url,
                json={"query": query, "variables": variables},
            )
            resp.raise_for_status()
            data = resp.json()["data"]["Page"]["media"]
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise AniListSearchError(str(exc)) from exc

        result = []
        for item in data:
            if await is_nsfw_anilist(item) and not include_adult:
                continue
            result.append(await build_anime_from_anilist_item(item, fallback_to_anilist_id=False))
        return result

    async def get_by_anilist_id(self, anime_id: int) -> Anime | None:
        """Fetch anime by AniList id.

        Args:
            anime_id: AniList anime identifier.

        Returns:
            Anime | None: The anime or None when unavailable.
        """
        return await self._get_by_media(
            variables={"id": anime_id},
            media_expression="Media(id: $id, type: ANIME)",
            fallback_to_anilist_id=True,
        )

    async def get_by_mal_id(self, anime_id: int) -> Anime | None:
        """Fetch anime by MAL id.

        Args:
            anime_id: MAL anime identifier.

        Returns:
            Anime | None: The anime or None when unavailable.
        """
        return await self._get_by_media(
            variables={"idMal": anime_id},
            media_expression="Media(idMal: $idMal, type: ANIME)",
            fallback_to_anilist_id=False,
        )

    async def _get_by_media(
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

    async def get_season_popular(
        self,
        *,
        year: int,
        season: str,
        limit: int,
    ) -> list[Anime]:
        """Fetch season popular anime.

        Args:
            year: Season year.
            season: Season name.
            limit: Maximum number of results.

        Returns:
            list[Anime]: Popular anime, or an empty list on failure.
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
                self.base_url,
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

        return [
            await build_anime_from_anilist_item(item, fallback_to_anilist_id=True) for item in data
        ]

    async def filter_catalog(
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
            limit: Maximum number of results.

        Returns:
            list[Anime]: Filtered and sorted anime, or an empty list on failure.
        """
        format_map = {
            "tv": "TV",
            "movie": "MOVIE",
            "ova": "OVA",
            "ona": "ONA",
            "special": "SPECIAL",
        }
        status_map = {"airing": "RELEASING", "complete": "FINISHED", "upcoming": "NOT_YET_RELEASED"}
        sort_map = {
            "rating": "SCORE_DESC",
            "popularity": "POPULARITY_DESC",
            "newest": "START_DATE_DESC",
            "title": "TITLE_ROMAJI",
        }

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
            query (__DECLARATIONS__) {
              Page(perPage: $perPage) {
                media(__ARGS__) {
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
            """.replace("__DECLARATIONS__", ", ".join(declarations))
            .replace("__ARGS__", " ".join(args))
            .replace("PLACEHOLDER_SORT", sort_map.get(sort, "SCORE_DESC"))
        )
        try:
            resp = await self.session.post(
                self.base_url,
                json={"query": query, "variables": variables},
            )
            resp.raise_for_status()
            data = resp.json().get("data", {}).get("Page", {}).get("media", [])
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return []

        result = []
        for item in data:
            if await is_nsfw_anilist(item):
                continue
            result.append(await build_anime_from_anilist_item(item, fallback_to_anilist_id=True))
        return result
