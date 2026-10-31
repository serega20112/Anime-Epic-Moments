"""Добавление источника просмотра вручную."""

from __future__ import annotations

from backend.application.dto import AddWatchSourceCommand
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain import Translation, WatchSource


class AddWatchSourceUseCase:
    """Создаёт озвучку и источник просмотра для аниме."""

    def __init__(self, unit_of_work: UnitOfWorkInterface) -> None:
        """Инициализирует сценарий добавления источника просмотра.

        Args:
            unit_of_work: Граница транзакции создания озвучки и источника.
        """
        self._unit_of_work = unit_of_work

    async def execute(self, command: AddWatchSourceCommand) -> WatchSource:
        """Создаёт озвучку и источник просмотра внутри транзакции.

        Args:
            command: Команда добавления источника просмотра.

        Returns:
            WatchSource: Созданный источник с идентификатором.
        """
        async with self._unit_of_work as uow:
            repository = uow.repository(WatchRepository)
            translation = await repository.add_translation(
                Translation(
                    anime_id=command.anime_id,
                    name=command.translation_name,
                    translation_type=command.translation_type,
                    language=command.language,
                )
            )
            return await repository.add_source(
                WatchSource(
                    anime_id=command.anime_id,
                    episode=command.episode,
                    translation_id=translation.id or 0,
                    provider_name=command.provider_name,
                    source_name=command.source_name,
                    stream_url=command.stream_url,
                    quality_label=command.quality_label,
                    source_type=command.source_type,
                )
            )
