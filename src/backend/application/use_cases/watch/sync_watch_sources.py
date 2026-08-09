from backend.application.use_cases.watch.result import WatchResult
from backend.domain.services import AnimeApiClientInterface as AnimeApiClient
from backend.domain.services import (
    WatchSourceSyncServiceInterface as WatchSourceSyncService,
)


class SyncWatchSourcesUseCase:
    """Подтягивает источники просмотра из внешнего провайдера."""

    def __init__(
            self,
            anime_api_client: AnimeApiClient,
            watch_source_sync_service: WatchSourceSyncService,
    ):
        self.anime_api_client = anime_api_client
        self.watch_source_sync_service = watch_source_sync_service

    async def execute(self, anime_id: int, episode: int, force: bool = False) -> WatchResult:
        if not await self.watch_source_sync_service.is_enabled():
            return WatchResult.failure("provider_not_configured", status_code=400)
        anime = await self.anime_api_client.get_by_id(anime_id)
        sources = await self.watch_source_sync_service.sync_for_anime(
            anime_id=anime_id,
            anime=anime,
            episode=episode,
            force=force,
        )
        return WatchResult.success(
            {
                "enabled": True,
                "sources_count": len(sources),
                "provider_names": await self.watch_source_sync_service.get_enabled_provider_names(),
            }
        )
