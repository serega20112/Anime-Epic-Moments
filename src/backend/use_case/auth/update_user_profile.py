"""Use case обновления профиля пользователя."""

from src.backend.domain.user.entity import User
from src.backend.domain.user.exceptions import InvalidUsernameError
from src.backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from src.backend.repository.user_repository import UserRepository


class UserNotFoundError(Exception):
    pass


class InvalidProfileDataError(Exception):
    pass


class UpdateUserProfileUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        self.user_repo = user_repo
        self.profile_overview_cache = profile_overview_cache

    async def execute(self, user_id: int, username: str, avatar_url: str | None) -> User:
        """Обновляет имя и аватар текущего пользователя."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError("Пользователь не найден")

        cleaned_username = username.strip()
        if not cleaned_username:
            raise InvalidProfileDataError("Имя пользователя не может быть пустым")

        try:
            user.change_username(cleaned_username)
        except InvalidUsernameError as exc:
            raise InvalidProfileDataError(str(exc)) from exc

        normalized_avatar = avatar_url.strip() if avatar_url else None
        user.update_avatar(normalized_avatar)
        updated_user = await self.user_repo.update(user)
        if self.profile_overview_cache is not None:
            await self.profile_overview_cache.invalidate_overview(user_id)
        return updated_user
