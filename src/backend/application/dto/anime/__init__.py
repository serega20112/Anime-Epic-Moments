from backend.application.dto.anime.anime_catalog_result import AnimeCatalogResult
from backend.application.dto.anime.autocomplete_anime_query import AutocompleteAnimeQuery
from backend.application.dto.anime.filter_anime_catalog_query import FilterAnimeCatalogQuery
from backend.application.dto.anime.get_season_popular_query import GetSeasonPopularQuery
from backend.application.dto.anime.search_anime_by_description_query import (
    SearchAnimeByDescriptionQuery,
)
from backend.application.dto.anime.search_anime_query import SearchAnimeQuery

__all__ = [
    "AnimeCatalogResult",
    "AutocompleteAnimeQuery",
    "FilterAnimeCatalogQuery",
    "GetSeasonPopularQuery",
    "SearchAnimeByDescriptionQuery",
    "SearchAnimeQuery",
]
