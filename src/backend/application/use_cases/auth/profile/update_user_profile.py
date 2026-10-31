"""Сценарий обновления профиля пользователя."""

from __future__ import annotations

from backend.application.dto import UpdateProfileCommand
from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.services.profile_overview_cache import (
    ProfileOverviewCacheInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.auth.result import AuthResult
from backend.domain.exceptions import ValidationError

PROFILE_PAGE = "auth.profile_page"
USER_NOT_FOUND_MESSAGE = "Пользователь не найден"
EMPTY_USERNAME_MESSAGE = "Имя пользователя не может быть пустым"
PROFILE_UPDATED_MESSAGE = "Профиль обновлён"


class UpdateUserProfileUseCase:
    """Обновляет имя, аватар, статус и видимость активности пользователя."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        profile_overview_cache: ProfileOverviewCacheInterface,
    ) -> None:
        """Собрать сценарий изменения профиля.

        Args:
            unit_of_work: Граница транзакции сохранения профиля.
            profile_overview_cache: Кэш обзора профиля этого пользователя.
        """
        self._unit_of_work = unit_of_work
        self._profile_overview_cache = profile_overview_cache

    async def execute(self, command: UpdateProfileCommand) -> AuthResult:
        """Изменить профиль текущего пользователя внутри транзакции.

        Правила имени и длины статуса принадлежат агрегату, поэтому сценарий
        не пересказывает их, а превращает любую доменную ошибку в возврат на
        страницу профиля с текстом нарушения.

        Args:
            command: Команда правки профиля с именем, аватаром и статусом.

        Returns:
            AuthResult: Успех с переходом на профиль либо отказ обратно на профиль.
        """
        cleaned_username = command.username.strip()
        if not cleaned_username:
            return AuthResult.failure(EMPTY_USERNAME_MESSAGE, PROFILE_PAGE)

        async with self._unit_of_work as uow:
            repository = uow.repository(UserRepository)
            user = await repository.get_by_id(command.user_id)
            if user is None:
                return AuthResult.failure(USER_NOT_FOUND_MESSAGE, PROFILE_PAGE)
            try:
                user.change_username(cleaned_username)
                user.change_status(command.status)
            except ValidationError as error:
                return AuthResult.failure(str(error), PROFILE_PAGE)
            user.update_avatar(command.avatar_url.strip() if command.avatar_url else None)
            user.toggle_watch_activity_visibility(command.show_watch_activity)
            user.toggle_recent_episodes_visibility(command.show_recent_episodes)
            updated_user = await repository.update(user)

        await self._profile_overview_cache.invalidate_overview(command.user_id)
        return AuthResult.success(
            data=updated_user,
            message=PROFILE_UPDATED_MESSAGE,
            redirect_endpoint=PROFILE_PAGE,
        )
