from starlette import status

from backend.application.dto import SaveViewingMomentCommand
from backend.application.interface.repositories.moment_repository import MomentRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.moment.result import MomentResult
from backend.domain import ViewingMoment


class SaveViewingMomentUseCase:
    """Creates or updates a draft viewing moment."""

    def __init__(self, moment_repo: MomentRepository, unit_of_work: UnitOfWorkInterface):
        self.moment_repo = moment_repo
        self.unit_of_work = unit_of_work

    async def execute(self, command: SaveViewingMomentCommand) -> MomentResult:
        """Persist a moment within a transaction.

        Args:
            command: Save viewing moment command.

        Returns:
            MomentResult: Result with the persisted moment.
        """
        if command.moment_id is None and (command.episode <= 0 or command.timestamp < 0):
            return await MomentResult.failure(
                "invalid_moment", status_code=status.HTTP_400_BAD_REQUEST
            )
        async with self.unit_of_work:
            moment = await self.moment_repo.save_moment(
                ViewingMoment(
                    user_id=command.user_id,
                    anime_id=command.anime_id,
                    episode=command.episode,
                    timestamp=command.timestamp,
                    watch_source_id=command.watch_source_id,
                    caption=command.caption,
                    sticker=command.sticker,
                    screenshot_url=command.screenshot_url,
                    id=command.moment_id,
                )
            )
            return await MomentResult.success(moment)
