from src.backend.domain.watch.entity import Translation, WatchSource
from src.backend.repository.watch_repository import WatchRepository


class AddWatchSourceUseCase:
    """Создает озвучку и источник просмотра для аниме."""

    def __init__(self, watch_repo: WatchRepository):
        self.watch_repo = watch_repo

    def execute(
        self,
        anime_id: int,
        episode: int,
        translation_name: str,
        translation_type: str,
        provider_name: str,
        source_name: str,
        stream_url: str,
        quality_label: str,
        language: str = "ru",
        source_type: str = "stream",
    ) -> WatchSource:
        """Создает озвучку и источник просмотра для аниме."""
        translation = self.watch_repo.add_translation(
            Translation(
                anime_id=anime_id,
                name=translation_name,
                translation_type=translation_type,
                language=language,
            )
        )
        return self.watch_repo.add_source(
            WatchSource(
                anime_id=anime_id,
                episode=episode,
                translation_id=translation.id or 0,
                provider_name=provider_name,
                source_name=source_name,
                stream_url=stream_url,
                quality_label=quality_label,
                source_type=source_type,
            )
        )
