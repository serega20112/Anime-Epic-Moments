"""Запрос ссылки на восстановление пароля."""

from __future__ import annotations

from backend.application.dto import RequestPasswordResetCommand
from backend.application.interface.services.jwt_service import JWTServiceInterface
from backend.application.interface.services.password_reset_mailer import (
    PasswordResetMailerInterface,
)
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.policies import PasswordResetPolicy
from backend.application.use_cases.auth.result import AuthResult
from backend.application.use_cases.auth.user_lookup import find_user_by_email
from backend.domain.policies.user_credentials_policy import normalize_email

PASSWORD_RESET_CONFIRM_PATH = "/auth/password-reset/confirm"


class RequestPasswordResetUseCase:
    """Создаёт ссылку сброса пароля и отправляет её на email пользователя."""

    def __init__(
        self,
        unit_of_work: UnitOfWorkInterface,
        jwt_service: JWTServiceInterface,
        mailer: PasswordResetMailerInterface,
        policy: PasswordResetPolicy,
    ) -> None:
        """Инициализирует сценарий запроса сброса пароля.

        Args:
            unit_of_work: Граница транзакции чтения пользователя.
            jwt_service: Сервис JWT-токенов.
            mailer: Сервис отправки почты.
            policy: Узкая политика сброса: адрес приложения и срок токена.
        """
        self._unit_of_work = unit_of_work
        self._jwt_service = jwt_service
        self._mailer = mailer
        self._policy = policy

    async def execute(self, command: RequestPasswordResetCommand) -> AuthResult:
        """Запрашивает ссылку сброса пароля.

        Ответ идентичен независимо от наличия пользователя, чтобы не
        разглашать информацию о существовании аккаунта.

        Args:
            command: Адрес почты и базовый URL для формирования ссылки.

        Returns:
            AuthResult: Всегда success на страницу запроса.
        """
        email = normalize_email(command.email)
        user = await find_user_by_email(self._unit_of_work, email)
        if user is None:
            return AuthResult.success(redirect_endpoint="auth.password_reset_request_page")

        token = await self._jwt_service.create_password_reset_token(
            user_id=user.id, expires_minutes=self._policy.expire_minutes
        )
        base_url = (command.base_url or self._policy.base_url).rstrip("/")
        await self._mailer.send_reset_email(
            user.email,
            f"{base_url}{PASSWORD_RESET_CONFIRM_PATH}?token={token}",
        )
        return AuthResult.success(redirect_endpoint="auth.password_reset_request_page")
