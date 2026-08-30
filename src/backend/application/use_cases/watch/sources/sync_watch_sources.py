import asyncio

from starlette import status

from backend.application.interface.services import AnimeApiClientInterface as AnimeApiClient
from backend.application.interface.services import (
    WatchSourceSyncServiceInterface as WatchSourceSyncService,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.watch.result import WatchResult


class SyncWatchSourcesUseCase:
    """Подтягивает источники просмотра из внешнего провайдера."""

    def __init__(
        self,
        anime_api_client: AnimeApiClient,
        watch_source_sync_service: WatchSourceSyncService,
        unit_of_work: UnitOfWorkInterface,
    ):
        self.anime_api_client = anime_api_client
        self.watch_source_sync_service = watch_source_sync_service
        self.unit_of_work = unit_of_work

    async def execute(self, anime_id: int, episode: int, force: bool = False) -> WatchResult:
        """Sync watch sources within a transaction."""
        async with self.unit_of_work:
            return await self._execute(anime_id, episode, force)

    async def _execute(self, anime_id: int, episode: int, force: bool = False) -> WatchResult:
        if not await self.watch_source_sync_service.is_enabled():
            return await WatchResult.failure(
                "provider_not_configured", status_code=status.HTTP_400_BAD_REQUEST
            )
        anime = await self.anime_api_client.get_by_id(anime_id)
        try:
            sources = await asyncio.wait_for(
                self.watch_source_sync_service.sync_for_anime(
                    anime_id=anime_id,
                    anime=anime,
                    episode=episode,
                    force=force,
                ),
                timeout=10,
            )
        except TimeoutError:
            return await WatchResult.failure(
                "provider_timeout", status_code=status.HTTP_504_GATEWAY_TIMEOUT
            )
        if len(sources) == 0:
            return await WatchResult.failure(
                "no_sources_found", status_code=status.HTTP_404_NOT_FOUND
            )
        if not await self._episode_available_for_any_translation(anime, episode):
            return await WatchResult.failure(
                "episode_not_available_for_translation", status_code=status.HTTP_404_NOT_FOUND
            )
        return await WatchResult.success(
            {
                "enabled": True,
                "sources_count": len(sources),
                "provider_names": await self.watch_source_sync_service.get_enabled_provider_names(),
            }
        )

    async def _episode_available_for_any_translation(self, anime, episode: int) -> bool:
        """Проверяет, доступна ли серия хотя бы у одной озвучки.

        Fail-fast: если серия отсутствует у всех озвучек (по карте
        доступности провайдера), возвращается False — вызывающий код
        отдаёт 404 вместо подмены контента похожим тайтлом.

        Args:
            anime: Сущность Anime или None.
            episode: Номер серии.

        Returns:
            bool: True, если карта доступности пуста (провайдер не поддерживает)
            или серия есть хотя бы у одной озвучки.
        """
        if anime is None or not getattr(anime, "title", None):
            return True
        availability = await self.watch_source_sync_service.get_translations_availability(
            title=anime.title,
            year=anime.year,
            shikimori_id=self._shikimori_id(anime),
            genres=anime.genres,
        )
        if not availability:
            return True
        return any(record.has_episode(episode) for record in availability)

    @staticmethod
    def _shikimori_id(anime) -> int | None:
        """Извлекает shikimori_id (MAL-id) из external_id, если это число.

        Args:
            anime: Сущность Anime.

        Returns:
            int | None: MAL-id или None, если external_id не числовой
            (например, AniList-id) — тогда строгая адресация невозможна.
        """
        external_id = str(getattr(anime, "external_id", "") or "").strip()
        if not external_id.isdigit():
            return None
        return int(external_id)
