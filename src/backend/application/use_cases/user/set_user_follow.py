from backend.application.use_cases.user.result import UserResult
from backend.domain import UserRepository
from backend.domain.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)


class SetUserFollowUseCase:
    """Создает или удаляет подписку между пользователями."""

    def __init__(
            self,
            user_repo: UserRepository,
            profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        self.user_repo = user_repo
        self.profile_overview_cache = profile_overview_cache

    async def execute(
            self,
            follower_user_id: int,
            followed_user_id: int,
            follow: bool,
    ) -> UserResult:
        target_user = await self.user_repo.get_by_id(followed_user_id)
        if target_user is None:
            return UserResult.failure("Пользователь для подписки не найден", status_code=404)
        if follow:
            result = await self.user_repo.follow(follower_user_id, followed_user_id)
        else:
            result = await self.user_repo.unfollow(follower_user_id, followed_user_id)
        if self.profile_overview_cache is not None:
            await self.profile_overview_cache.invalidate_overview(int(follower_user_id))
            await self.profile_overview_cache.invalidate_overview(int(followed_user_id))
        return UserResult.success(result)
