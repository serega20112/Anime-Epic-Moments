from typing import Any, List

import requests
from src.backend.domain.anime.entity import Anime
from src.backend.infrastructure.cache.ttl_cache import TTLCache


class AnimeApiClient:
    """
    Клиент для получения данных аниме из Jikan API и AniList GraphQL.
    Возвращает объекты домена Anime.
    """

    def __init__(self):
        self.jikan_base = "https://api.jikan.moe/v4"
        self.anilist_base = "https://graphql.anilist.co"
        self.session = requests.Session()
        self.session.trust_env = False
        self._title_search_cache = TTLCache[tuple[str, str, int, bool], list[Anime]](
            ttl_seconds=300,
            max_entries=256,
        )
        self._description_search_cache = TTLCache[
            tuple[str, str, int | None, int | None, int | None, bool, int],
            list[Anime],
        ](
            ttl_seconds=300,
            max_entries=256,
        )
        self._anime_cache = TTLCache[int, Anime | None](
            ttl_seconds=1800,
            max_entries=1024,
        )
        self._season_cache = TTLCache[tuple[int, str, int], list[Anime]](
            ttl_seconds=900,
            max_entries=64,
        )
        self._top_cache = TTLCache[int, list[Anime]](
            ttl_seconds=900,
            max_entries=32,
        )

    # ----------------- Jikan -----------------
    def search_by_title(
        self, title: str, limit: int = 10, include_adult: bool = False
    ) -> List[Anime]:
        """
        Поиск аниме по названию через Jikan.
        """
        sanitized_title = self._sanitize_query(title)
        if not sanitized_title:
            return []
        cache_key = (
            "search_by_title",
            sanitized_title.lower(),
            int(limit),
            bool(include_adult),
        )
        if self._title_search_cache.contains(cache_key):
            return list(self._title_search_cache.get(cache_key) or [])
        url = f"{self.jikan_base}/anime"
        params = {"q": sanitized_title, "limit": limit}
        try:
            resp = self.session.get(url, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json().get("data", [])
        except (requests.RequestException, ValueError, KeyError, TypeError):
            return list(self._title_search_cache.set(cache_key, []))

        result = []
        for item in data:
            if self._is_nsfw_jikan(item) and not include_adult:
                continue
            result.append(self._build_anime_from_jikan_item(item))
        return list(self._title_search_cache.set(cache_key, result))

    def get_season_popular(
        self, year: int, season: str, limit: int = 10
    ) -> List[Anime]:
        """
        Получение популярных аниме сезона через Jikan.
        season: winter, spring, summer, fall
        """
        cache_key = (int(year), str(season).strip().lower(), int(limit))
        if self._season_cache.contains(cache_key):
            return list(self._season_cache.get(cache_key) or [])
        url = f"{self.jikan_base}/seasons/{year}/{season}"
        try:
            resp = self.session.get(url, timeout=20)
            resp.raise_for_status()
            data = resp.json().get("data", [])[:limit]
        except (requests.RequestException, ValueError, KeyError, TypeError):
            return list(self._season_cache.set(cache_key, []))

        result = []
        for item in data:
            result.append(self._build_anime_from_jikan_item(item))
        return list(self._season_cache.set(cache_key, result))

    # ----------------- AniList GraphQL -----------------
    def search_by_description(
        self,
        description: str,
        year_from: int | None = None,
        year_to: int | None = None,
        min_rating: int | None = None,
        include_adult: bool = False,
        limit: int = 10,
    ) -> List[Anime]:
        """
        Поиск аниме по описанию через AniList GraphQL.
        """
        query = """
        query ($search: String, $perPage: Int, $isAdult: Boolean) {
          Page(perPage: $perPage) {
            media(search: $search, type: ANIME, isAdult: $isAdult) {
              id
              idMal
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
        cache_key = (
            "search_by_description",
            sanitized_description.lower(),
            year_from,
            year_to,
            min_rating,
            bool(include_adult),
            int(limit),
        )
        if self._description_search_cache.contains(cache_key):
            return list(self._description_search_cache.get(cache_key) or [])
        variables: dict[str, object] = {
            "search": sanitized_description,
            "perPage": limit,
            "isAdult": None if include_adult else False,
        }
        try:
            resp = self.session.post(
                self.anilist_base,
                json={"query": query, "variables": variables},
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()["data"]["Page"]["media"]
        except (requests.RequestException, KeyError, TypeError, ValueError):
            fallback = self.search_by_title(
                title=sanitized_description, limit=limit, include_adult=include_adult
            )
            return list(self._description_search_cache.set(cache_key, fallback))

        result = []
        for item in data:
            if self._is_nsfw_anilist(item) and not include_adult:
                continue
            season_year = item.get("seasonYear")
            average_score = item.get("averageScore")
            normalized_score = (
                (average_score / 10)
                if isinstance(average_score, (int, float))
                else None
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
        return list(self._description_search_cache.set(cache_key, result))

    def get_by_id(self, anime_id: int) -> Anime | None:
        """Получает аниме по id с приоритетом MAL/Jikan и fallback на AniList."""
        anime_id = int(anime_id)
        if self._anime_cache.contains(anime_id):
            return self._anime_cache.get(anime_id)
        url = f"{self.jikan_base}/anime/{anime_id}"
        try:
            resp = self.session.get(url, timeout=20)
            resp.raise_for_status()
            item = resp.json().get("data")
            if not item:
                return self._anime_cache.set(anime_id, self._get_by_anilist_id(anime_id))
        except requests.HTTPError as error:
            status_code = error.response.status_code if error.response else None
            if status_code == 404:
                return self._anime_cache.set(
                    anime_id, self._get_by_anilist_id(anime_id)
                )
            anime = self._get_by_mal_id_via_anilist(anime_id)
            return self._anime_cache.set(
                anime_id, anime or self._get_by_anilist_id(anime_id)
            )
        except (requests.RequestException, ValueError, KeyError, TypeError):
            anime = self._get_by_mal_id_via_anilist(anime_id)
            return self._anime_cache.set(
                anime_id, anime or self._get_by_anilist_id(anime_id)
            )

        return self._anime_cache.set(anime_id, self._build_anime_from_jikan_item(item))

    def _get_by_mal_id_via_anilist(self, anime_id: int) -> Anime | None:
        return self._get_by_anilist_media(
            variables={"idMal": anime_id},
            media_expression="Media(idMal: $idMal, type: ANIME)",
            fallback_to_anilist_id=False,
        )

    def get_top_anime(self, limit: int = 25) -> List[Anime]:
        """Получает список популярных аниме через Jikan top."""
        cache_key = int(limit)
        if self._top_cache.contains(cache_key):
            return list(self._top_cache.get(cache_key) or [])
        url = f"{self.jikan_base}/top/anime"
        try:
            resp = self.session.get(url, params={"limit": limit}, timeout=20)
            resp.raise_for_status()
            data = resp.json().get("data", [])
        except (requests.RequestException, ValueError, KeyError, TypeError):
            return list(self._top_cache.set(cache_key, []))

        result = []
        for item in data:
            result.append(self._build_anime_from_jikan_item(item))
        return list(self._top_cache.set(cache_key, result))

    def _get_by_anilist_id(self, anime_id: int) -> Anime | None:
        """Best-effort fallback для старых записей, сохраненных с AniList id."""
        return self._get_by_anilist_media(
            variables={"id": anime_id},
            media_expression="Media(id: $id, type: ANIME)",
            fallback_to_anilist_id=True,
        )

    def _get_by_anilist_media(
        self,
        variables: dict[str, int],
        media_expression: str,
        fallback_to_anilist_id: bool,
    ) -> Anime | None:
        query = """
        query ($id: Int, $idMal: Int) {
          media: PLACEHOLDER_MEDIA_EXPRESSION {
            id
            idMal
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
            resp = self.session.post(
                self.anilist_base,
                json={"query": query, "variables": variables},
                timeout=20,
            )
            resp.raise_for_status()
            item = resp.json().get("data", {}).get("media")
        except (requests.RequestException, ValueError, KeyError, TypeError):
            return None
        if not item:
            return None
        return self._build_anime_from_anilist_item(
            item,
            fallback_to_anilist_id=fallback_to_anilist_id,
        )

    def _passes_filters(
        self,
        season_year: int | None,
        normalized_score: float | None,
        year_from: int | None,
        year_to: int | None,
        min_rating: int | None,
    ) -> bool:
        """Проверяет, попадает ли аниме под фильтры года и минимального рейтинга."""
        if year_from is not None and (season_year is None or season_year < year_from):
            return False
        if year_to is not None and (season_year is None or season_year > year_to):
            return False
        if min_rating is not None and (
            normalized_score is None or normalized_score < min_rating
        ):
            return False
        return True

    def _sanitize_query(self, query: str | None) -> str:
        """Очищает поисковый запрос от служебных и невалидных символов."""
        if not query:
            return ""
        normalized = str(query).replace("\x00", " ").replace("\u0000", " ")
        normalized = " ".join(normalized.split())
        return normalized.strip()

    def _build_anime_from_jikan_item(self, item: dict[str, Any]) -> Anime:
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
        )

    def _build_anime_from_anilist_item(
        self,
        item: dict[str, Any],
        fallback_to_anilist_id: bool,
    ) -> Anime:
        title_data = item.get("title", {}) or {}
        average_score = item.get("averageScore")
        normalized_score = (
            (average_score / 10)
            if isinstance(average_score, (int, float))
            else None
        )
        mal_id = self._normalize_numeric_id(item.get("idMal"))
        anilist_id = self._normalize_numeric_id(item.get("id"))
        external_id = mal_id or (anilist_id if fallback_to_anilist_id else "")

        return Anime(
            external_id=external_id,
            title=self._pick_anilist_title(title_data),
            description=item.get("description"),
            genres=[
                str(genre).strip() for genre in (item.get("genres", []) or []) if genre
            ],
            year=item.get("seasonYear"),
            rating=normalized_score,
            cover_url=item.get("coverImage", {}).get("large"),
        )

    def _pick_anilist_title(self, title_data: dict[str, Any]) -> str:
        for key in ("romaji", "english", "native"):
            value = str(title_data.get(key) or "").strip()
            if value:
                return value
        return "Unknown anime"

    def _normalize_numeric_id(self, value: Any) -> str:
        if isinstance(value, bool) or value is None:
            return ""
        try:
            numeric_value = int(value)
        except (TypeError, ValueError):
            return ""
        return str(numeric_value) if numeric_value > 0 else ""

    def _is_nsfw_jikan(self, item: dict) -> bool:
        """Определяет NSFW по rating строке Jikan."""
        rating_text = str(item.get("rating") or "").lower()
        nsfw_markers = ("hentai", "explicit", "porn", "rx")
        return any(marker in rating_text for marker in nsfw_markers)

    def _is_nsfw_anilist(self, item: dict) -> bool:
        """Определяет NSFW по isAdult и жанру Hentai в AniList."""
        if bool(item.get("isAdult")):
            return True
        genres = item.get("genres", []) or []
        return any(str(genre).strip().lower() == "hentai" for genre in genres)
