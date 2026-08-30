"""Jikan API anime client."""

from __future__ import annotations

import httpx

from backend.domain.entities.anime.anime import Anime
from backend.infrastructure.external.mapping.anime import (
    build_anime_from_jikan_item,
    is_nsfw_jikan,
)

JIKAN_BASE_URL = "https://api.jikan.moe/v4"


class JikanAnimeClient:
    """Fetch anime data from the Jikan API.

    Only performs network I/O against the Jikan REST API and delegates payload
    mapping to the pure mapping helpers. Errors degrade to empty results
    because callers treat this client as a primary source with fallbacks.
    """

    genre_id_map = {
        "Action": 1,
        "Adventure": 2,
        "Cars": 3,
        "Comedy": 4,
        "Dementia": 5,
        "Demons": 6,
        "Mystery": 7,
        "Drama": 8,
        "Ecchi": 9,
        "Fantasy": 10,
        "Gender Bender": 11,
        "Harem": 35,
        "Hentai": 12,
        "Historical": 13,
        "Horror": 14,
        "Josei": 43,
        "Kids": 15,
        "Magic": 16,
        "Martial Arts": 17,
        "Mecha": 18,
        "Music": 19,
        "Parody": 20,
        "Psychological": 40,
        "Romance": 22,
        "Samurai": 21,
        "School": 23,
        "Sci-Fi": 24,
        "Seinen": 42,
        "Shoujo": 25,
        "Shounen": 27,
        "Slice of Life": 36,
        "Space": 29,
        "Sports": 30,
        "Super Power": 31,
        "Supernatural": 37,
        "Thriller": 41,
        "Vampire": 32,
    }

    genre_id_by_lower = {name.lower(): genre_id for name, genre_id in genre_id_map.items()}

    def __init__(self, session: httpx.AsyncClient, base_url: str = JIKAN_BASE_URL):
        """Initialize the client.

        Args:
            session: Shared HTTP client owned by the orchestrating facade.
            base_url: Jikan API base URL.
        """
        self.session = session
        self.base_url = base_url

    async def search_by_title(
        self,
        title: str,
        limit: int = 10,
        include_adult: bool = False,
    ) -> list[Anime]:
        """Search anime by title.

        Args:
            title: Search query.
            limit: Maximum number of results.
            include_adult: Whether adult content is allowed.

        Returns:
            list[Anime]: Matching anime, or an empty list on failure.
        """
        url = f"{self.base_url}/anime"
        params = {"q": title, "limit": limit}
        try:
            resp = await self.session.get(url, params=params)
            resp.raise_for_status()
            data = resp.json().get("data", [])
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return []

        result = []
        for item in data:
            if await is_nsfw_jikan(item) and not include_adult:
                continue
            result.append(await build_anime_from_jikan_item(item))
        return result

    async def get_by_id(self, anime_id: int) -> Anime | None:
        """Fetch a single anime by id.

        Args:
            anime_id: Jikan anime identifier.

        Returns:
            Anime | None: The anime or None when unavailable.
        """
        url = f"{self.base_url}/anime/{anime_id}"
        try:
            resp = await self.session.get(url)
            resp.raise_for_status()
            item = resp.json().get("data")
            if not item:
                return None
            return await build_anime_from_jikan_item(item)
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return None

    async def get_season_popular(self, year: int, season: str, limit: int = 10) -> list[Anime]:
        """Fetch popular anime of a season.

        Args:
            year: Season year.
            season: Season name (winter, spring, summer, fall).
            limit: Maximum number of results.

        Returns:
            list[Anime]: Popular anime, or an empty list on failure.
        """
        url = f"{self.base_url}/seasons/{year}/{season}"
        try:
            resp = await self.session.get(url)
            resp.raise_for_status()
            data = resp.json().get("data", [])[:limit]
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return []

        return [await build_anime_from_jikan_item(item) for item in data]

    async def get_top_anime(self, limit: int = 25) -> list[Anime]:
        """Fetch popular anime through the Jikan top endpoint.

        Args:
            limit: Maximum number of results.

        Returns:
            list[Anime]: Popular anime, or an empty list on failure.
        """
        url = f"{self.base_url}/top/anime"
        try:
            resp = await self.session.get(url, params={"limit": limit})
            resp.raise_for_status()
            data = resp.json().get("data", [])
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return []

        return [await build_anime_from_jikan_item(item) for item in data]

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
        """Filter and sort anime through the Jikan /anime endpoint.

        Args:
            genre: Comma-separated genre names.
            media_type: Format filter value.
            status: Status filter value.
            year_from: Optional lower bound release year.
            year_to: Optional upper bound release year.
            min_score: Optional minimum normalized rating.
            sort: Normalized sort key.
            order: Sorting direction.
            limit: Maximum number of results.

        Returns:
            list[Anime]: Filtered and sorted anime, or an empty list on failure.
        """
        params: dict[str, object] = {"limit": limit}
        genre_ids = []
        for genre_name in str(genre or "").split(","):
            genre_id = self.genre_id_by_lower.get(genre_name.strip().lower())
            if genre_id:
                genre_ids.append(genre_id)
        if genre_ids:
            params["genres"] = ",".join(str(genre_id) for genre_id in genre_ids)
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
            resp = await self.session.get(f"{self.base_url}/anime", params=params)
            resp.raise_for_status()
            data = resp.json().get("data", [])
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return []

        result = []
        for item in data:
            result.append(await build_anime_from_jikan_item(item))
        return result
