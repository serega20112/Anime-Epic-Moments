from secrets import randbelow

from backend.application.interface.services import (
    EmailVerificationMailerInterface as EmailVerificationMailer,
)
from backend.application.interface.services import (
    EmailVerificationStoreInterface as EmailVerificationStore,
)
from backend.application.use_cases.auth.result import AuthResult
from backend.domain import PendingEmailVerification


class PendingEmailVerificationNotFoundError(Exception):
    """Raised when no pending registration exists for an email."""


class ResendEmailVerificationUseCase:
    """Перевыпускает код подтверждения для ожидающей регистрации."""

    def __init__(
        self,
        verification_store: EmailVerificationStore,
        mailer: EmailVerificationMailer,
    ):
        """Initialize the use case.

        Args:
            verification_store: Verification code store.
            mailer: Email verification mailer.
        """
        self.verification_store = verification_store
        self.mailer = mailer

    async def execute(self, email: str) -> AuthResult:
        """Regenerate and resend a verification code.

        Args:
            email: Normalized user email.

        Returns:
            AuthResult: Success with the email or failure redirect.
        """
        normalized_email = str(email or "").strip().lower()
        payload = await self.verification_store.get(normalized_email)
        if payload is None:
            return await AuthResult.failure(
                "Не найдена ожидающая регистрация для этого email.",
                "auth.verify_email_page",
                redirect_email=normalized_email,
            )
        refreshed = PendingEmailVerification(
            email=payload.email,
            username=payload.username,
            password_hash=payload.password_hash,
            code=await self._generate_code(),
            theme=payload.theme,
        )
        await self.verification_store.save(refreshed)
        await self.mailer.send_verification_code(
            refreshed.email,
            refreshed.code,
            theme=refreshed.theme,
        )
        return await AuthResult.success(
            data=normalized_email,
            message="Новый код подтверждения отправлен.",
            redirect_endpoint="auth.verify_email_page",
            redirect_email=normalized_email,
        )

    async def _generate_code(self) -> str:
        return f"{randbelow(1000000):06d}"
