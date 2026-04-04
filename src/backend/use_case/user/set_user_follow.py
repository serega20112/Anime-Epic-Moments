from src.backend.infrastructure.repositories.user_repository import UserRepository
from src.backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache


class SetUserFollowUseCase:
    """Создает или удаляет подписку между пользователями."""

    def __init__(
        self,
        user_repo: UserRepository,
        profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        self.user_repo = user_repo
        self.profile_overview_cache = profile_overview_cache

    def execute(
        self,
        follower_user_id: int,
        followed_user_id: int,
        follow: bool,
    ) -> bool:
        target_user = self.user_repo.get_by_id(followed_user_id)
        if target_user is None:
            raise ValueError("Пользователь для подписки не найден")
        if follow:
            result = self.user_repo.follow(follower_user_id, followed_user_id)
        else:
            result = self.user_repo.unfollow(follower_user_id, followed_user_id)
        if self.profile_overview_cache is not None:
            self.profile_overview_cache.invalidate_overview(int(follower_user_id))
            self.profile_overview_cache.invalidate_overview(int(followed_user_id))
        return result
