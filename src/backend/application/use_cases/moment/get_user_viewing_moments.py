from backend.application.use_cases.moment.result import MomentResult
from backend.domain import MomentRepository


class GetUserViewingMomentsUseCase:
    """Lists draft viewing moments of a user."""

    def __init__(self, moment_repo: MomentRepository):
        self.moment_repo = moment_repo

    async def execute(self, user_id: int) -> MomentResult:
        """Fetch the user's draft moments.

        Args:
            user_id: Owner user identifier.

        Returns:
            MomentResult: Result with the list of moments.
        """
        moments = await self.moment_repo.get_moments_by_user(user_id)
        return await MomentResult.success(moments)
