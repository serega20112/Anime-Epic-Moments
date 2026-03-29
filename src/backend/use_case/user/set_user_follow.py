from src.backend.infrastructure.repositories.user_repository import UserRepository


class SetUserFollowUseCase:
    """Создает или удаляет подписку между пользователями."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

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
            return self.user_repo.follow(follower_user_id, followed_user_id)
        return self.user_repo.unfollow(follower_user_id, followed_user_id)
