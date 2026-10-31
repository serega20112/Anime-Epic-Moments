"""Сценарий запроса кода подтверждения адреса почты."""

from __future__ import annotations

from backend.application.dto import RegisterCommand
from backend.application.interface.services import (
    EmailVerificationMailerInterface,
    EmailVerificationStoreInterface,
    PasswordServiceInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.auth.result import AuthResult
from backend.application.use_cases.auth.user_lookup import find_user_by_email
from backend.domain import PendingEmailVerification
from backend.domain.policies.email_verification_policy import (
    generate_verification_code,
    normalize_theme,
)
from backend.domain.policies.user_credentials_policy import normalize_email


class RequestEmailVerificationUseCase:
    """Создаёт pending-регистрацию и отправляет код подтверждения email."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        password_service: PasswordServiceInterface,
        verification_store: EmailVerificationStoreInterface,
        mailer: EmailVerificationMailerInterface,
    ) -> None:
        """Инициализирует сценарий запроса кода подтверждения.

        Args:
            unit_of_work: Граница транзакции проверки занятого email.
            password_service: Сервис хеширования паролей.
            verification_store: Хранилище кодов подтверждения.
            mailer: Сервис отправки почты.
        """
        self._unit_of_work = unit_of_work
        self._password_service = password_service
        self._verification_store = verification_store
        self._mailer = mailer

    async def execute(self, command: RegisterCommand) -> AuthResult:
        """Начинает регистрацию, запрашивая код подтверждения email.

        Args:
            command: Команда регистрации с почтой, паролем, именем и темой.

        Returns:
            AuthResult: Success с pending-записью или failure с редиректом.
        """
        email = normalize_email(command.email)
        if await self._email_taken(email):
            return AuthResult.failure(
                f"Пользователь с email {email} уже существует",
                "auth.register_page",
            )

        payload = PendingEmailVerification(
            email=email,
            username=str(command.username or "").strip(),
            password_hash=await self._password_service.hash_password(command.password),
            code=generate_verification_code(),
            theme=normalize_theme(command.theme),
        )
        await self._verification_store.save(payload)
        await self._mailer.send_verification_code(
            payload.email,
            payload.code,
            theme=payload.theme,
        )
        return AuthResult.success(
            data=email,
            message=(
                "Мы отправили код подтверждения на почту. Введи его, чтобы завершить регистрацию."
            ),
            redirect_endpoint="auth.verify_email_page",
            redirect_email=email,
        )

    async def _email_taken(self, email: str) -> bool:
        """Проверить, занят ли адрес почты существующим аккаунтом.

        Args:
            email: Нормализованный адрес почты.

        Returns:
            bool: True, если пользователь с таким адресом уже зарегистрирован.
        """
        return await find_user_by_email(self._unit_of_work, email) is not None
