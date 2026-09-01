"""Use case обновления профиля пользователя."""

from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface as ProfileOverviewCache,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.auth.result import AuthResult
from backend.domain.aggregates.user.exceptions import InvalidUsernameError


class UserNotFoundError(Exception):
    """Raised when the authenticated user does not exist."""


class InvalidProfileDataError(Exception):
    """Raised when submitted profile data is invalid."""


class UpdateUserProfileUseCase:
    """Обновляет имя и аватар текущего пользователя."""

    def __init__(
        self,
        user_repo: UserRepository,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCache | None = None,
    ):
        """Initialize the use case.

        Args:
            user_repo: User repository port.
            profile_overview_cache: Optional profile cache.
            unit_of_work: Transaction boundary.
        """
        self.user_repo = user_repo
        self.profile_overview_cache = profile_overview_cache
        self.unit_of_work = unit_of_work

    async def execute(
        self,
        user_id: int,
        username: str,
        avatar_url: str | None,
        status: str | None = None,
        show_watch_activity: bool = True,
        show_recent_episodes: bool = True,
    ) -> AuthResult:
        """Update the user profile within a transaction."""
        async with self.unit_of_work:
            return await self._execute(
                user_id,
                username,
                avatar_url,
                status,
                show_watch_activity,
                show_recent_episodes,
            )

    async def _execute(
        self,
        user_id: int,
        username: str,
        avatar_url: str | None,
        status: str | None,
        show_watch_activity: bool,
        show_recent_episodes: bool,
    ) -> AuthResult:
        """Обновляет профиль текущего пользователя.

        Args:
            user_id: Authenticated user id.
            username: New username.
            avatar_url: New avatar url.
            status: New status text or None.
            show_watch_activity: Публиковать ли динамику просмотра.
            show_recent_episodes: Публиковать ли недавно просмотренное.

        Returns:
            AuthResult: Success toward the profile page or failure back to it.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return await AuthResult.failure("Пользователь не найден", "auth.profile_page")

        cleaned_username = username.strip()
        if not cleaned_username:
            return await AuthResult.failure(
                "Имя пользователя не может быть пустым",
                "auth.profile_page",
            )

        try:
            user.change_username(cleaned_username)
            user.change_status(status)
        except (InvalidUsernameError, ValueError) as exc:
            return await AuthResult.failure(str(exc), "auth.profile_page")

        normalized_avatar = avatar_url.strip() if avatar_url else None
        user.update_avatar(normalized_avatar)
        user.toggle_watch_activity_visibility(show_watch_activity)
        user.toggle_recent_episodes_visibility(show_recent_episodes)
        updated_user = await self.user_repo.update(user)
        if self.profile_overview_cache is not None:
            await self.profile_overview_cache.invalidate_overview(user_id)
        return await AuthResult.success(
            data=updated_user,
            message="Профиль обновлён",
            redirect_endpoint="auth.profile_page",
        )
