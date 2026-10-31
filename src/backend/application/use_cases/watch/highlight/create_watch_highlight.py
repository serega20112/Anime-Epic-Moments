"""Сценарий создания хайлайта из плеера."""

from __future__ import annotations

from starlette import status

from backend.application.dto import CreateHighlightCommand, CreateWatchHighlightCommand
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.highlight.crud.create_highlight import CreateHighlightUseCase
from backend.application.use_cases.result import UseCaseResult
from backend.domain import HighlightContext


class CreateWatchHighlightUseCase:
    """Создаёт хайлайт из плеера и сохраняет контекст проигрывания."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        create_highlight_use_case: CreateHighlightUseCase,
    ) -> None:
        """Инициализирует сценарий создания хайлайта из плеера.

        Args:
            unit_of_work: Граница транзакции хайлайта и его контекста.
            create_highlight_use_case: Сценарий создания хайлайта.
        """
        self._unit_of_work = unit_of_work
        self._create_highlight_use_case = create_highlight_use_case

    async def execute(self, command: CreateWatchHighlightCommand) -> UseCaseResult:
        """Создаёт хайлайт из плеера внутри транзакции.

        Args:
            command: Команда создания хайлайта с контекстом плеера.

        Returns:
            UseCaseResult: Результат с созданным хайлайтом.
        """
        if self._missing_fields(command):
            return UseCaseResult.failure("invalid_payload", status_code=status.HTTP_400_BAD_REQUEST)
        async with self._unit_of_work as uow:
            highlight_result = await self._create_highlight_use_case.execute(
                CreateHighlightCommand(
                    user_id=command.user_id,
                    anime_id=command.anime_id,
                    episode=command.episode,
                    start_timestamp=command.start_timestamp,
                    end_timestamp=command.end_timestamp,
                    title=command.title,
                    category=command.category,
                    description=command.description,
                    is_spoiler=command.is_spoiler,
                    emotion=command.emotion,
                )
            )
            if not highlight_result.ok:
                return UseCaseResult.failure(
                    highlight_result.error or "Не удалось создать хайлайт",
                    status_code=highlight_result.status_code,
                )
            await uow.repository(WatchRepository).add_highlight_context(
                HighlightContext(
                    highlight_id=highlight_result.data.id or 0,
                    watch_source_id=command.watch_source_id,
                    translation_id=command.translation_id,
                    title=command.title,
                    original_title=command.original_title,
                )
            )
        return UseCaseResult.success(highlight_result.data, status_code=status.HTTP_201_CREATED)

    @staticmethod
    def _missing_fields(command: CreateWatchHighlightCommand) -> bool:
        """Проверить, хватает ли полей плеера для создания хайлайта.

        Args:
            command: Команда создания хайлайта из плеера.

        Returns:
            bool: True, если хотя бы одно обязательное значение отсутствует.
        """
        values = (
            command.episode,
            command.watch_source_id,
            command.translation_id,
            command.start_timestamp,
            command.end_timestamp,
        )
        return any(value is None for value in values)
