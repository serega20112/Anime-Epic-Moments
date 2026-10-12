"""Use case for browsing anime through Anixart-style filters."""

from __future__ import annotations

import asyncio

from backend.application.dto.anime import AnimeCatalogResult, FilterAnimeCatalogQuery
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.services import AnimeApiClientInterface as AnimeApiClient
from backend.application.interface.services import (
    WatchSourceSyncServiceInterface as WatchSourceSyncService,
)
from backend.domain.entities.anime.anime import Anime
from backend.domain.value_objects.anime.genre_facet import GenreFacet
from backend.domain.value_objects.anime.genre_filter import (
    GenreFilter,
    GenreMatchMode,
    normalize_genre,
)

MAX_PER_PAGE = 100
DEFAULT_PER_PAGE = 25
ALLOWED_PER_PAGE = (10, 25, 50, 100)
FACET_LIMIT = 60
DUB_FETCH_MULTIPLIER = 4
WINDOW_LIMIT = 400


class FilterAnimeCatalogUseCase:
    """Browse anime by genre, format, status, year, rating and sort.

    Provider APIs narrow the catalog with OR semantics only, so the exact
    genre semantics requested by the user (all selected genres, or any of
    them) are enforced here with :class:`GenreFilter`. Titles can also be
    restricted to those that actually have a voice-over, which is resolved
    from the local translations table first and from the provider
    availability map afterwards.
    """

    def __init__(
        self,
        api_client: AnimeApiClient,
        watch_repository: WatchRepository,
        watch_source_sync_service: WatchSourceSyncService,
    ):
        """Initialize the use case.

        Args:
            api_client: Anime API client.
            watch_repository: Watch repository for local translation lookup.
            watch_source_sync_service: Watch source sync service for
                availability checks.
        """
        self.api_client = api_client
        self.watch_repository = watch_repository
        self.watch_source_sync_service = watch_source_sync_service

    async def execute(self, query: FilterAnimeCatalogQuery) -> AnimeCatalogResult:
        """Return one page of anime matching the requested filters.

        Args:
            query: Filter query DTO.

        Returns:
            AnimeCatalogResult: Requested page, pagination metadata and the
                genre facets observed in the scanned results.
        """
        per_page = self._per_page(query.per_page)
        genre_filter = GenreFilter.from_values(query.genres, query.genre_mode)
        needs_window = query.has_dub is True or genre_filter.mode is GenreMatchMode.ALL

        if needs_window:
            return await self._execute_over_window(query, genre_filter, per_page)

        page = await self.api_client.filter_catalog(
            genres=query.genres,
            media_type=query.media_type,
            status=query.status,
            year_from=query.year_from,
            year_to=query.year_to,
            min_score=query.min_score,
            sort=query.sort,
            order=query.order,
            page=query.page,
            per_page=per_page,
        )
        items = [anime for anime in page.items if genre_filter.matches(anime.genres)]
        return AnimeCatalogResult(
            items=tuple(items),
            page=page.page,
            per_page=page.per_page,
            total=page.total,
            total_is_exact=True,
            genre_facets=_build_facets(page.items),
        )

    async def _execute_over_window(
        self,
        query: FilterAnimeCatalogQuery,
        genre_filter: GenreFilter,
        per_page: int,
    ) -> AnimeCatalogResult:
        """Filter a bounded provider window and slice the requested page.

        Providers cannot express conjunctive genre matching or dubbing
        availability, so a wider window is fetched once and narrowed locally.

        Args:
            query: Filter query DTO.
            genre_filter: Exact genre semantics to enforce.
            per_page: Normalized page size.

        Returns:
            AnimeCatalogResult: Requested page of the narrowed window.
        """
        window = self._window_size(query.page, per_page, query.has_dub is True)
        provider_page = await self.api_client.filter_catalog(
            genres=query.genres,
            media_type=query.media_type,
            status=query.status,
            year_from=query.year_from,
            year_to=query.year_to,
            min_score=query.min_score,
            sort=query.sort,
            order=query.order,
            page=1,
            per_page=window,
        )
        scanned = list(provider_page.items)

        candidates = [anime for anime in scanned if genre_filter.matches(anime.genres)]
        if query.has_dub is True and candidates:
            candidates = await self._keep_dubbed(candidates)

        start = (max(1, query.page) - 1) * per_page
        items = candidates[start : start + per_page]
        return AnimeCatalogResult(
            items=tuple(items),
            page=max(1, query.page),
            per_page=per_page,
            total=len(candidates),
            total_is_exact=len(scanned) < window,
            genre_facets=_build_facets(scanned),
        )

    @staticmethod
    def _per_page(value: int) -> int:
        """Normalize the requested page size.

        Args:
            value: Requested page size.

        Returns:
            int: One of the supported page sizes.
        """
        try:
            requested = int(value)
        except (TypeError, ValueError):
            return DEFAULT_PER_PAGE
        if requested in ALLOWED_PER_PAGE:
            return requested
        return min(ALLOWED_PER_PAGE, key=lambda size: abs(size - requested))

    @staticmethod
    def _window_size(page: int, per_page: int, needs_dub: bool) -> int:
        """Compute how many provider items must be scanned to serve a page.

        Args:
            page: Requested page number.
            per_page: Normalized page size.
            needs_dub: Whether dubbing availability narrows the results.

        Returns:
            int: Number of items to request from the provider.
        """
        required = max(1, page) * per_page
        if needs_dub:
            required *= DUB_FETCH_MULTIPLIER
        return min(WINDOW_LIMIT, max(per_page, required))

    async def _keep_dubbed(self, candidates: list[Anime]) -> list[Anime]:
        """Keep only titles that have at least one available translation.

        Args:
            candidates: Titles scanned from the provider.

        Returns:
            list[Anime]: Titles with a voice-over, in the original order.
        """
        flags = await asyncio.gather(*[self._has_translation(anime) for anime in candidates])
        return [anime for anime, has_translation in zip(candidates, flags) if has_translation]

    async def _has_translation(self, anime: Anime) -> bool:
        """Check whether an anime has at least one available translation.

        Args:
            anime: Anime entity.

        Returns:
            bool: True when the anime has a voice-over.
        """
        anime_id = self._anime_id(anime)
        if anime_id is not None:
            try:
                local_translations = await self.watch_repository.get_translations(anime_id)
                if local_translations:
                    return True
            except Exception:
                pass

        if not anime.title:
            return False
        try:
            availability = await self.watch_source_sync_service.get_translations_availability(
                title=anime.title,
                year=anime.year,
                shikimori_id=self._shikimori_id(anime),
                genres=anime.genres,
            )
            return bool(availability)
        except Exception:
            return False

    @staticmethod
    def _anime_id(anime: Anime) -> int | None:
        """Extract the numeric anime id used in the local database.

        Args:
            anime: Anime entity.

        Returns:
            int | None: Numeric external id or None.
        """
        external_id = str(getattr(anime, "external_id", "") or "").strip()
        if not external_id.isdigit():
            return None
        return int(external_id)

    @staticmethod
    def _shikimori_id(anime: Anime) -> int | None:
        """Extract shikimori_id (MAL-id) from external_id, if it is numeric.

        Args:
            anime: Anime entity.

        Returns:
            int | None: MAL-id or None when external_id is not numeric.
        """
        return FilterAnimeCatalogUseCase._anime_id(anime)


def _build_facets(animes) -> tuple[GenreFacet, ...]:
    """Count genres across the scanned titles, most frequent first.

    Args:
        animes: Titles returned by the provider.

    Returns:
        tuple[GenreFacet, ...]: Genres present in the results, capped to keep
            the filter panel compact.
    """
    counters: dict[str, int] = {}
    labels: dict[str, str] = {}
    for anime in animes:
        for genre in getattr(anime, "genres", None) or ():
            label = str(genre).strip()
            key = normalize_genre(label)
            if not key or key in counters:
                continue
            counters[key] = counters.get(key, 0) + 1
            labels[key] = label
    ordered = sorted(counters.items(), key=lambda item: (-item[1], item[0]))
    return tuple(GenreFacet(name=labels[key], count=count) for key, count in ordered[:FACET_LIMIT])
