from backend.domain import Translation, WatchRepository, WatchSource
from backend.domain.unit_of_work import UnitOfWorkInterface


class AddWatchSourceUseCase:
    """Создает озвучку и источник просмотра для аниме."""

    def __init__(
        self,
        watch_repo: WatchRepository,
        unit_of_work: UnitOfWorkInterface,
    ):
        self.watch_repo = watch_repo
        self.unit_of_work = unit_of_work

    async def execute(
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
        """Create a translation and watch source within a transaction."""
        async with self.unit_of_work:
            return await self._execute(
                anime_id,
                episode,
                translation_name,
                translation_type,
                provider_name,
                source_name,
                stream_url,
                quality_label,
                language,
                source_type,
            )

    async def _execute(
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
        translation = await self.watch_repo.add_translation(
            Translation(
                anime_id=anime_id,
                name=translation_name,
                translation_type=translation_type,
                language=language,
            )
        )
        return await self.watch_repo.add_source(
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
