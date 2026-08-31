"""Use case for browsing anime through Anixart-style filters."""

from __future__ import annotations

import asyncio

from backend.application.dto.anime import FilterAnimeCatalogQuery
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.services import AnimeApiClientInterface as AnimeApiClient
from backend.application.interface.services import (
    WatchSourceSyncServiceInterface as WatchSourceSyncService,
)
from backend.domain.entities.anime.anime import Anime


class FilterAnimeCatalogUseCase:
    """Browse anime by genre, format, status, year, rating and sort.

    Only anime with at least one available translation (voice-over) are
    returned. The check first consults the local ``translations`` table and
    falls back to the external provider availability map when the title has
    not been synced yet.
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

    async def execute(self, query: FilterAnimeCatalogQuery) -> list[Anime]:
        """Return anime matching the requested filters.

        When query.has_dub is True, only titles with at least one available
        translation (voice-over) are returned. When has_dub is None or False,
        no additional filtering by translation availability is applied.

        Args:
            query: Filter query DTO.

        Returns:
            list[Anime]: Matching anime.
        """
        # If the caller doesn't require dubbing we can ask the API for exactly
        # as many items as requested and return them directly.
        if query.has_dub is not True:
            candidates = await self.api_client.filter_catalog(
                genre=query.genre,
                media_type=query.media_type,
                status=query.status,
                year_from=query.year_from,
                year_to=query.year_to,
                min_score=query.min_score,
                sort=query.sort,
                order=query.order,
                limit=int(query.limit),
            )
            return candidates or []

        # Caller requested only titles with voice-over: fetch more items
        # and filter them by availability of translations.
        fetch_limit = max(int(query.limit) * 3, 60)
        candidates = await self.api_client.filter_catalog(
            genre=query.genre,
            media_type=query.media_type,
            status=query.status,
            year_from=query.year_from,
            year_to=query.year_to,
            min_score=query.min_score,
            sort=query.sort,
            order=query.order,
            limit=fetch_limit,
        )
        if not candidates:
            return []

        # Проверяем наличие озвучки у каждого тайтла параллельно.
        availability_flags = await asyncio.gather(
            *[self._has_translation(anime) for anime in candidates]
        )
        filtered = [
            anime
            for anime, has_translation in zip(candidates, availability_flags)
            if has_translation
        ]
        filtered = filtered[: int(query.limit)]
        return filtered

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
