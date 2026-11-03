"""Сценарии входа через Google и привязки/отвязки аккаунта.

Проверку подлинности ID-токена выполняет внешний порт, а решение о том,
найдён ли уже пользователь по стабильному идентификатору или почте и создавать
ли новый аккаунт, принимает этот сценарий. Именование нового пользователя и
генерация служебного пароля живут здесь, поэтому presentation остаётся тонким.
"""

from __future__ import annotations

import re
import secrets

from starlette import status

from backend.application.dto.auth import (
    GoogleSignInCommand,
    LinkGoogleAccountCommand,
    UnlinkGoogleAccountCommand,
)
from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.services import (
    GoogleAuthClientInterface,
    GoogleIdentity,
    PasswordServiceInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.result import UseCaseResult
from backend.domain import User
from backend.domain.policies.user_credentials_policy import (
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
)

INVALID_TOKEN_MESSAGE = "Недействительный токен Google"
GOOGLE_LINK_TAKEN_MESSAGE = "Этот аккаунт Google уже привязан к другому пользователю"
USERNAME_PADDING = "user"
DISALLOWED_USERNAME_CHARS = re.compile(r"[^a-z0-9._-]+")


class GoogleSignInUseCase:
    """Находит или создаёт пользователя по подтверждённому ID-токену Google."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        google_client: GoogleAuthClientInterface,
        password_service: PasswordServiceInterface,
    ) -> None:
        """Инициализирует сценарий входа через Google.

        Args:
            unit_of_work: Граница транзакции поиска и создания пользователя.
            google_client: Порт проверки ID-токена Google.
            password_service: Сервис хеширования служебного пароля.
        """
        self._unit_of_work = unit_of_work
        self._google_client = google_client
        self._password_service = password_service

    async def execute(self, command: GoogleSignInCommand) -> UseCaseResult:
        """Проверить токен и вернуть пользователя для выпуска токенов приложения.

        Args:
            command: ID-токен Google.

        Returns:
            UseCaseResult: Найденный или созданный пользователь либо отказ 401.
        """
        identity = await self._google_client.verify_id_token(command.id_token)
        if identity is None:
            return UseCaseResult.failure(
                INVALID_TOKEN_MESSAGE, status_code=status.HTTP_401_UNAUTHORIZED
            )
        async with self._unit_of_work as uow:
            repository = uow.repository(UserRepository)
            existing = await repository.get_by_google_subject(identity.subject)
            if existing is not None:
                return UseCaseResult.success(existing)
            by_email = await repository.get_by_email(identity.email)
            if by_email is not None:
                by_email.link_google(identity.subject)
                return UseCaseResult.success(await repository.update(by_email))
            created = await repository.add(await self._new_user(identity))
        return UseCaseResult.success(created)

    async def _new_user(self, identity: GoogleIdentity) -> User:
        """Собрать нового пользователя из подтверждённой личности Google.

        Args:
            identity: Подтверждённая личность из ID-токена.

        Returns:
            User: Агрегат с уникальным служебным паролем и привязанным Google.
        """
        placeholder = await self._password_service.hash_password(secrets.token_urlsafe(32))
        user = User(
            email=identity.email,
            username=_username_from_email(identity.email),
            password_hash=placeholder,
            avatar_url=identity.picture or None,
        )
        user.link_google(identity.subject)
        return user


class LinkGoogleAccountUseCase:
    """Привязывает подтверждённый аккаунт Google к пользователю сессии."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        google_client: GoogleAuthClientInterface,
    ) -> None:
        """Инициализирует сценарий привязки Google.

        Args:
            unit_of_work: Граница транзакции изменения привязки.
            google_client: Порт проверки ID-токена Google.
        """
        self._unit_of_work = unit_of_work
        self._google_client = google_client

    async def execute(self, command: LinkGoogleAccountCommand) -> UseCaseResult:
        """Проверить токен и привязать Google к пользователю, если он свободен.

        Args:
            command: Пользователь сессии и ID-токен Google.

        Returns:
            UseCaseResult: Успех либо отказ 401 при неверном токене и 409 при
                занятой привязке.
        """
        identity = await self._google_client.verify_id_token(command.id_token)
        if identity is None:
            return UseCaseResult.failure(
                INVALID_TOKEN_MESSAGE, status_code=status.HTTP_401_UNAUTHORIZED
            )
        async with self._unit_of_work as uow:
            repository = uow.repository(UserRepository)
            holder = await repository.get_by_google_subject(identity.subject)
            if holder is not None and int(holder.id or 0) != int(command.user_id):
                return UseCaseResult.failure(
                    GOOGLE_LINK_TAKEN_MESSAGE, status_code=status.HTTP_409_CONFLICT
                )
            user = await repository.get_by_id(command.user_id)
            if user is None:
                return UseCaseResult.failure(
                    "Пользователь не найден", status_code=status.HTTP_404_NOT_FOUND
                )
            user.link_google(identity.subject)
            await repository.update(user)
        return UseCaseResult.success({"google_linked": True})


class UnlinkGoogleAccountUseCase:
    """Отвязывает аккаунт Google от пользователя сессии."""

    def __init__(self, unit_of_work: UnitOfWorkInterface) -> None:
        """Инициализирует сценарий отвязки Google.

        Args:
            unit_of_work: Граница транзакции изменения привязки.
        """
        self._unit_of_work = unit_of_work

    async def execute(self, command: UnlinkGoogleAccountCommand) -> UseCaseResult:
        """Снять привязку Google с пользователя сессии.

        Args:
            command: Пользователь сессии.

        Returns:
            UseCaseResult: Успех либо отказ 404 при отсутствии пользователя.
        """
        async with self._unit_of_work as uow:
            repository = uow.repository(UserRepository)
            user = await repository.get_by_id(command.user_id)
            if user is None:
                return UseCaseResult.failure(
                    "Пользователь не найден", status_code=status.HTTP_404_NOT_FOUND
                )
            user.unlink_google()
            await repository.update(user)
        return UseCaseResult.success({"google_linked": False})


def _username_from_email(email: str) -> str:
    """Собрать допустимое имя пользователя из адреса почты.

    Берёт локальную часть почты, оставляет разрешённые символы и приводит длину
    к требованиям агрегата пользователя: короткое имя дополняется, длинное
    усекается.

    Args:
        email: Подтверждённый адрес почты из ID-токена Google.

    Returns:
        str: Имя пользователя допустимой длины.
    """
    local = email.split("@", 1)[0].lower()
    cleaned = DISALLOWED_USERNAME_CHARS.sub("", local)[:USERNAME_MAX_LENGTH]
    if len(cleaned) < USERNAME_MIN_LENGTH:
        cleaned = (cleaned + USERNAME_PADDING)[:USERNAME_MAX_LENGTH]
    return cleaned
