"""Сценарий сохранения сессии просмотра."""

from __future__ import annotations

from starlette import status

from backend.application.dto import SaveViewingSessionCommand
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult
from backend.domain import ViewingSession


class SaveViewingSessionUseCase:
    """Сохраняет текущую позицию просмотра пользователя."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCacheInterface,
    ) -> None:
        """Инициализирует сценарий сохранения сессии просмотра.

        Args:
            unit_of_work: Граница транзакции сохранения сессии.
            profile_overview_cache: Кэш обзора профиля пользователя.
        """
        self._unit_of_work = unit_of_work
        self._profile_overview_cache = profile_overview_cache

    async def execute(self, command: SaveViewingSessionCommand) -> UseCaseResult:
        """Сохраняет сессию просмотра внутри транзакции.

        Args:
            command: Команда сохранения сессии просмотра.

        Returns:
            UseCaseResult: Результат с сохранённой сессией.
        """
        if command.episode is None or command.watch_source_id is None:
            return UseCaseResult.failure("invalid_payload", status_code=status.HTTP_400_BAD_REQUEST)
        session = ViewingSession(
            user_id=command.user_id,
            anime_id=command.anime_id,
            episode=command.episode,
            watch_source_id=command.watch_source_id,
            position_seconds=float(command.position_seconds or 0.0),
            volume=float(command.volume or 1.0),
            quality_label=str(command.quality_label or "Auto"),
            is_paused=bool(command.is_paused),
        )
        async with self._unit_of_work as uow:
            saved = await uow.repository(WatchRepository).upsert_session(session)
        await self._profile_overview_cache.invalidate_overview(command.user_id)
        return UseCaseResult.success(saved)
