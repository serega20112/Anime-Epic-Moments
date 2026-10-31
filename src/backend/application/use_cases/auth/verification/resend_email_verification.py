"""Повторная отправка кода подтверждения почты."""

from __future__ import annotations

from backend.application.dto import ResendVerificationCommand
from backend.application.interface.services import (
    EmailVerificationMailerInterface,
    EmailVerificationStoreInterface,
)
from backend.application.use_cases.auth.result import AuthResult
from backend.domain import PendingEmailVerification
from backend.domain.policies.email_verification_policy import generate_verification_code
from backend.domain.policies.user_credentials_policy import normalize_email


class ResendEmailVerificationUseCase:
    """Перевыпускает код подтверждения для ожидающей регистрации."""

    def __init__(
        self,
        verification_store: EmailVerificationStoreInterface,
        mailer: EmailVerificationMailerInterface,
    ) -> None:
        """Инициализирует сценарий перевыпуска кода подтверждения.

        Args:
            verification_store: Хранилище кодов подтверждения.
            mailer: Сервис отправки почты.
        """
        self._verification_store = verification_store
        self._mailer = mailer

    async def execute(self, command: ResendVerificationCommand) -> AuthResult:
        """Перевыпускает и отправляет код подтверждения заново.

        Args:
            command: Команда повторной отправки с адресом почты.

        Returns:
            AuthResult: Success с email или failure с редиректом.
        """
        email = normalize_email(command.email)
        payload = await self._verification_store.get(email)
        if payload is None:
            return AuthResult.failure(
                "Не найдена ожидающая регистрация для этого email.",
                "auth.verify_email_page",
                redirect_email=email,
            )
        refreshed = PendingEmailVerification(
            email=payload.email,
            username=payload.username,
            password_hash=payload.password_hash,
            code=generate_verification_code(),
            theme=payload.theme,
        )
        await self._verification_store.save(refreshed)
        await self._mailer.send_verification_code(
            refreshed.email,
            refreshed.code,
            theme=refreshed.theme,
        )
        return AuthResult.success(
            data=email,
            message="Новый код подтверждения отправлен.",
            redirect_endpoint="auth.verify_email_page",
            redirect_email=email,
        )
