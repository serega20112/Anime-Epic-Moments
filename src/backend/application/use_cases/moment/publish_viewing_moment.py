from starlette import status

from backend.application.dto import CreateHighlightCommand, PublishViewingMomentCommand
from backend.application.interface.repositories.moment_repository import MomentRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.highlight.crud.create_highlight import CreateHighlightUseCase
from backend.application.use_cases.moment.result import MomentResult

MOMENT_WINDOW_SECONDS = 15.0


class PublishViewingMomentUseCase:
    """Publishes a draft viewing moment as a highlight."""

    def __init__(
        self,
        moment_repo: MomentRepository,
        create_highlight: CreateHighlightUseCase,
        unit_of_work: UnitOfWorkInterface,
    ):
        self.moment_repo = moment_repo
        self.create_highlight = create_highlight
        self.unit_of_work = unit_of_work

    async def execute(self, command: PublishViewingMomentCommand) -> MomentResult:
        """Convert the moment into a highlight and remove the draft.

        Args:
            command: Publish viewing moment command.

        Returns:
            MomentResult: Result with the created highlight.
        """
        async with self.unit_of_work:
            return await self._execute(command)

    async def _execute(self, command: PublishViewingMomentCommand) -> MomentResult:
        moment = await self.moment_repo.get_moment(command.moment_id, command.user_id)
        if moment is None:
            return await MomentResult.failure(
                "moment_not_found", status_code=status.HTTP_404_NOT_FOUND
            )

        half_window = MOMENT_WINDOW_SECONDS / 2
        title = command.title or moment.caption or f"Момент {moment.episode} серии"
        category = command.category or moment.sticker
        highlight_result = await self.create_highlight.execute(
            CreateHighlightCommand(
                user_id=command.user_id,
                anime_id=moment.anime_id,
                episode=moment.episode,
                start_timestamp=max(0.0, moment.timestamp - half_window),
                end_timestamp=moment.timestamp + half_window,
                title=title,
                category=category,
                description=command.description or "",
                is_spoiler=command.is_spoiler,
                emotion=command.emotion,
            )
        )
        if not highlight_result.ok:
            return await MomentResult.failure(
                str(highlight_result.error or "publish_failed"),
                status_code=highlight_result.status_code,
            )
        await self.moment_repo.delete_moment(moment.id, command.user_id)
        return await MomentResult.success(
            highlight_result.data, status_code=status.HTTP_201_CREATED
        )
