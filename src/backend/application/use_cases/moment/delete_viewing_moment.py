from backend.application.use_cases.moment.result import MomentResult
from backend.domain import MomentRepository
from backend.domain.unit_of_work import UnitOfWorkInterface


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
                return await MomentResult.failure("moment_not_found", status_code=404)
            return await MomentResult.success({"deleted": True})
