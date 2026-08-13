from backend.application.dto import CreateHighlightCommand
from backend.application.dto import CreateWatchHighlightCommand
from backend.application.use_cases.watch.result import WatchResult
from backend.application.use_cases.highlight.create_highlight import CreateHighlightUseCase
from backend.domain import HighlightContext
from backend.domain import WatchRepository
from backend.domain.unit_of_work import UnitOfWorkInterface


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
            return WatchResult.failure("invalid_payload", status_code=400)
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
            return WatchResult.failure(
                highlight_result.error or "Не удалось создать хайлайт",
                status_code=highlight_result.status_code,
            )
        await self.watch_repo.add_highlight_context(
            HighlightContext(
                highlight_id=highlight_result.data.id or 0,
                watch_source_id=command.watch_source_id,
                translation_id=command.translation_id,
                title=command.title,
            )
        )
        return WatchResult.success(highlight_result.data, status_code=201)
