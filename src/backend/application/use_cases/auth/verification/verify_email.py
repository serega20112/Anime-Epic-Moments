"""Подтверждение адреса почты одноразовым кодом."""

from __future__ import annotations

from backend.application.dto import VerifyEmailCommand
from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.services import (
    EmailVerificationStoreInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.auth.result import AuthResult
from backend.domain import User
from backend.domain.policies.user_credentials_policy import normalize_email

VERIFICATION_PAGE = "auth.verify_email_page"
EXPIRED_CODE_MESSAGE = "Код подтверждения истёк. Запроси новый."
INVALID_CODE_MESSAGE = "Неверный код подтверждения."


class VerifyEmailUseCase:
    """Подтверждает email кодом и создаёт пользователя после успешной проверки."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        verification_store: EmailVerificationStoreInterface,
    ) -> None:
        """Инициализирует сценарий подтверждения email.

        Args:
            unit_of_work: Граница транзакции создания пользователя.
            verification_store: Хранилище кодов подтверждения.
        """
        self._unit_of_work = unit_of_work
        self._verification_store = verification_store

    async def execute(self, command: VerifyEmailCommand) -> AuthResult:
        """Подтверждает email-код и создаёт пользователя в рамках транзакции.

        Args:
            command: Адрес почты и код подтверждения из письма.

        Returns:
            AuthResult: Success с созданным пользователем или failure с редиректом.
        """
        email = normalize_email(command.email)
        code = str(command.code or "").strip()
        payload = await self._verification_store.get(email)
        if payload is None:
            return AuthResult.failure(EXPIRED_CODE_MESSAGE, VERIFICATION_PAGE, redirect_email=email)
        if payload.code != code:
            return AuthResult.failure(INVALID_CODE_MESSAGE, VERIFICATION_PAGE, redirect_email=email)

        user = User(
            email=payload.email,
            username=payload.username,
            password_hash=payload.password_hash,
        )
        async with self._unit_of_work as uow:
            repository = uow.repository(UserRepository)
            if await repository.get_by_email(email) is not None:
                await self._verification_store.delete(email)
                return AuthResult.failure(
                    f"Пользователь с email {email} уже существует",
                    VERIFICATION_PAGE,
                    redirect_email=email,
                )
            created_user = await repository.add(user)
        await self._verification_store.delete(email)
        return AuthResult.success(
            data=created_user,
            message=f"Добро пожаловать, {created_user.username}!",
            redirect_endpoint="index.index",
        )
