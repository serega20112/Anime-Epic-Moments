from starlette import status

from backend.application.interface.repositories.moment_repository import MomentRepository
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.moment.result import MomentResult


class DeleteViewingMomentUseCase:
    """Deletes a draft viewing moment of the user."""

    def __init__(self, moment_repo: MomentRepository, unit_of_work: UnitOfWorkInterface):
        self.moment_repo = moment_repo
        self.unit_of_work = unit_of_work

    async def execute(self, moment_id: int, user_id: int) -> MomentResult:
        """Delete the moment within a transaction.

        Args:
            moment_id: Moment identifier.
            user_id: Owner user identifier.

        Returns:
            MomentResult: Result of the deletion.
        """
        async with self.unit_of_work:
            deleted = await self.moment_repo.delete_moment(moment_id, user_id)
            if not deleted:
                return await MomentResult.failure(
                    "moment_not_found", status_code=status.HTTP_404_NOT_FOUND
                )
            return await MomentResult.success({"deleted": True})
