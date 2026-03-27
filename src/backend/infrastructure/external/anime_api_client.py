import requests
from typing import List
from src.backend.domain.anime.entity import Anime


class AnimeApiClient:
    """
    Клиент для получения данных аниме из Jikan API и AniList GraphQL.
    Возвращает объекты домена Anime.
    """

    def __init__(self):
        self.jikan_base = "https://api.jikan.moe/v4"
        self.anilist_base = "https://graphql.anilist.co"

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
        url = f"{self.jikan_base}/anime"
        params = {"q": sanitized_title, "limit": limit}
        try:
            resp = requests.get(
                url, params=params, proxies={"http": None, "https": None}, timeout=20
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
        except (requests.RequestException, ValueError, KeyError, TypeError):
            return []

        result = []
        for item in data:
            if self._is_nsfw_jikan(item) and not include_adult:
                continue
            result.append(
                Anime(
                    external_id=str(item.get("mal_id")),
                    title=item.get("title"),
                    description=item.get("synopsis"),
                    genres=[g["name"] for g in item.get("genres", [])],
                    year=item.get("year"),
                    rating=item.get("score"),
                    cover_url=item.get("images", {}).get("jpg", {}).get("image_url"),
                )
            )
        return result

    def get_season_popular(
        self, year: int, season: str, limit: int = 10
    ) -> List[Anime]:
        """
        Получение популярных аниме сезона через Jikan.
        season: winter, spring, summer, fall
        """
        url = f"{self.jikan_base}/seasons/{year}/{season}"
        try:
            resp = requests.get(url, proxies={"http": None, "https": None}, timeout=20)
            resp.raise_for_status()
            data = resp.json().get("data", [])[:limit]
        except (requests.RequestException, ValueError, KeyError, TypeError):
            return []

        result = []
        for item in data:
            result.append(
                Anime(
                    external_id=str(item.get("mal_id")),
                    title=item.get("title"),
                    description=item.get("synopsis"),
                    genres=[g["name"] for g in item.get("genres", [])],
                    year=item.get("year"),
                    rating=item.get("score"),
                    cover_url=item.get("images", {}).get("jpg", {}).get("image_url"),
                )
            )
        return result

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
        query ($search: String, $perPage: Int) {
          Page(perPage: $perPage) {
            media(search: $search, type: ANIME) {
              id
              title { romaji }
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
        variables = {"search": sanitized_description, "perPage": limit}
        try:
            resp = requests.post(
                self.anilist_base,
                json={"query": query, "variables": variables},
                proxies={"http": None, "https": None},
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()["data"]["Page"]["media"]
        except (requests.RequestException, KeyError, TypeError, ValueError):
            return self.search_by_title(
                title=sanitized_description, limit=limit, include_adult=include_adult
            )

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
                Anime(
                    external_id=str(item.get("id")),
                    title=item.get("title", {}).get("romaji"),
                    description=item.get("description"),
                    genres=item.get("genres", []),
                    year=season_year,
                    rating=normalized_score,
                    cover_url=item.get("coverImage", {}).get("large"),
                )
            )
            if len(result) >= limit:
                break
        return result

    def get_by_id(self, anime_id: int) -> Anime | None:
        """Получает аниме по MAL id через Jikan."""
        url = f"{self.jikan_base}/anime/{anime_id}"
        try:
            resp = requests.get(url, proxies={"http": None, "https": None}, timeout=20)
            resp.raise_for_status()
            item = resp.json().get("data")
            if not item:
                return None
        except (requests.RequestException, ValueError, KeyError, TypeError):
            return None

        return Anime(
            external_id=str(item.get("mal_id")),
            title=item.get("title"),
            description=item.get("synopsis"),
            genres=[g["name"] for g in item.get("genres", [])],
            year=item.get("year"),
            rating=item.get("score"),
            cover_url=item.get("images", {}).get("jpg", {}).get("image_url"),
        )

    def get_top_anime(self, limit: int = 25) -> List[Anime]:
        """Получает список популярных аниме через Jikan top."""
        url = f"{self.jikan_base}/top/anime"
        try:
            resp = requests.get(
                url,
                params={"limit": limit},
                proxies={"http": None, "https": None},
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
        except (requests.RequestException, ValueError, KeyError, TypeError):
            return []

        result = []
        for item in data:
            result.append(
                Anime(
                    external_id=str(item.get("mal_id")),
                    title=item.get("title"),
                    description=item.get("synopsis"),
                    genres=[g["name"] for g in item.get("genres", [])],
                    year=item.get("year"),
                    rating=item.get("score"),
                    cover_url=item.get("images", {}).get("jpg", {}).get("image_url"),
                )
            )
        return result

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
