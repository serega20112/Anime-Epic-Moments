from starlette import status

from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.user.result import UserResult


class SetUserFollowUseCase:
    """Создает или удаляет подписку между пользователями."""

    def __init__(
        self,
        user_repo: UserRepository,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        self.user_repo = user_repo
        self.profile_overview_cache = profile_overview_cache
        self.unit_of_work = unit_of_work

    async def execute(
        self,
        follower_user_id: int,
        followed_user_id: int,
        follow: bool,
    ) -> UserResult:
        """Set a user follow within a transaction."""
        async with self.unit_of_work:
            return await self._execute(follower_user_id, followed_user_id, follow)

    async def _execute(
        self,
        follower_user_id: int,
        followed_user_id: int,
        follow: bool,
    ) -> UserResult:
        target_user = await self.user_repo.get_by_id(followed_user_id)
        if target_user is None:
            return await UserResult.failure(
                "Пользователь для подписки не найден", status_code=status.HTTP_404_NOT_FOUND
            )
        if follow:
            result = await self.user_repo.follow(follower_user_id, followed_user_id)
        else:
            result = await self.user_repo.unfollow(follower_user_id, followed_user_id)
        if self.profile_overview_cache is not None:
            await self.profile_overview_cache.invalidate_overview(int(follower_user_id))
            await self.profile_overview_cache.invalidate_overview(int(followed_user_id))
        return await UserResult.success(result)
