from src.backend.infrastructure.external.anime_api_client import AnimeApiClient
from src.backend.services.watch_source_sync_service import WatchSourceSyncService


class SyncWatchSourcesUseCase:
    """Подтягивает источники просмотра из внешнего провайдера."""

    def __init__(
        self,
        anime_api_client: AnimeApiClient,
        watch_source_sync_service: WatchSourceSyncService,
    ):
        self.anime_api_client = anime_api_client
        self.watch_source_sync_service = watch_source_sync_service

    def execute(
        self, anime_id: int, episode: int, force: bool = False
    ) -> dict[str, int | bool]:
        anime = self.anime_api_client.get_by_id(anime_id)
        if not self.watch_source_sync_service.is_enabled():
            return {"enabled": False, "sources_count": 0, "provider_names": []}

        sources = self.watch_source_sync_service.sync_for_anime(
            anime_id=anime_id,
            anime=anime,
            episode=episode,
            force=force,
        )
        return {
            "enabled": True,
            "sources_count": len(sources),
            "provider_names": self.watch_source_sync_service.get_enabled_provider_names(),
        }
