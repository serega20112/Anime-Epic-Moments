from starlette import status

from backend.application.dto import CreateHighlightCommand, CreateWatchHighlightCommand
from backend.application.interface.repositories.watch_repository import WatchRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.highlight.crud.create_highlight import CreateHighlightUseCase
from backend.application.use_cases.watch.result import WatchResult
from backend.domain import HighlightContext


class CreateWatchHighlightUseCase:
    """Создает хайлайт из плеера и сохраняет playback context."""

    def __init__(
        self,
        create_highlight_use_case: CreateHighlightUseCase,
        watch_repo: WatchRepository,
        unit_of_work: UnitOfWorkInterface,
    ):
        self.create_highlight_use_case = create_highlight_use_case
        self.watch_repo = watch_repo
        self.unit_of_work = unit_of_work

    async def execute(self, command: CreateWatchHighlightCommand) -> WatchResult:
        """Create a watch highlight within a transaction."""
        async with self.unit_of_work:
            return await self._execute(command)

    async def _execute(self, command: CreateWatchHighlightCommand) -> WatchResult:
        if (
            command.episode is None
            or command.watch_source_id is None
            or command.translation_id is None
            or command.start_timestamp is None
            or command.end_timestamp is None
        ):
            return await WatchResult.failure(
                "invalid_payload", status_code=status.HTTP_400_BAD_REQUEST
            )
        highlight_result = await self.create_highlight_use_case.execute(
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
            return await WatchResult.failure(
                highlight_result.error or "Не удалось создать хайлайт",
                status_code=highlight_result.status_code,
            )
        await self.watch_repo.add_highlight_context(
            HighlightContext(
                highlight_id=highlight_result.data.id or 0,
                watch_source_id=command.watch_source_id,
                translation_id=command.translation_id,
                title=command.title,
                original_title=command.original_title,
            )
        )
        return await WatchResult.success(highlight_result.data, status_code=status.HTTP_201_CREATED)
