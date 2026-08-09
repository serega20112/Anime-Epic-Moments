"""Use case обновления профиля пользователя."""

from backend.application.use_cases.auth.result import AuthResult
from backend.domain import UserRepository
from backend.domain.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)
from backend.domain.user.exceptions import InvalidUsernameError


class UserNotFoundError(Exception):
    """Raised when the authenticated user does not exist."""


class InvalidProfileDataError(Exception):
    """Raised when submitted profile data is invalid."""


class UpdateUserProfileUseCase:
    """Обновляет имя и аватар текущего пользователя."""

    def __init__(
            self,
            user_repo: UserRepository,
            profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        """Initialize the use case.

        Args:
            user_repo: User repository port.
            profile_overview_cache: Optional profile cache.
        """
        self.user_repo = user_repo
        self.profile_overview_cache = profile_overview_cache

    async def execute(self, user_id: int, username: str, avatar_url: str | None) -> AuthResult:
        """Обновляет имя и аватар текущего пользователя.

        Args:
            user_id: Authenticated user id.
            username: New username.
            avatar_url: New avatar url.

        Returns:
            AuthResult: Success toward the profile page or failure back to it.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return AuthResult.failure("Пользователь не найден", "auth.profile_page")

        cleaned_username = username.strip()
        if not cleaned_username:
            return AuthResult.failure(
                "Имя пользователя не может быть пустым",
                "auth.profile_page",
            )

        try:
            user.change_username(cleaned_username)
        except InvalidUsernameError as exc:
            return AuthResult.failure(str(exc), "auth.profile_page")

        normalized_avatar = avatar_url.strip() if avatar_url else None
        user.update_avatar(normalized_avatar)
        updated_user = await self.user_repo.update(user)
        if self.profile_overview_cache is not None:
            await self.profile_overview_cache.invalidate_overview(user_id)
        return AuthResult.success(
            data=updated_user,
            message="Профиль обновлён",
            redirect_endpoint="auth.profile_page",
        )
