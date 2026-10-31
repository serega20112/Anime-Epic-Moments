"""Сценарий регистрации нового пользователя."""

from __future__ import annotations

from backend.application.dto import RegisterCommand
from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.services import PasswordServiceInterface
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain import User


class EmailAlreadyExistsError(Exception):
    """Возникает, когда email уже зарегистрирован."""


class RegisterUserUseCase:
    """Создаёт нового пользователя, если email ещё не зарегистрирован."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        password_service: PasswordServiceInterface,
    ) -> None:
        """Инициализирует сценарий регистрации.

        Args:
            unit_of_work: Граница транзакции создания пользователя.
            password_service: Сервис хеширования паролей.
        """
        self._unit_of_work = unit_of_work
        self._password_service = password_service

    async def execute(self, command: RegisterCommand) -> User:
        """Регистрирует пользователя внутри транзакции.

        Args:
            command: Команда регистрации с почтой, паролем и именем.

        Returns:
            User: Сохранённый агрегат пользователя.

        Raises:
            EmailAlreadyExistsError: Если email уже зарегистрирован.
        """
        password_hash = await self._password_service.hash_password(command.password)
        user = User(
            email=command.email,
            username=command.username,
            password_hash=password_hash,
        )
        async with self._unit_of_work as uow:
            repository = uow.repository(UserRepository)
            if await repository.get_by_email(command.email):
                raise EmailAlreadyExistsError(
                    f"Пользователь с email {command.email} уже существует"
                )
            return await repository.add(user)
