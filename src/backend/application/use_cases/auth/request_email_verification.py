from secrets import randbelow

from backend.application.use_cases.auth.result import AuthResult
from backend.domain import PendingEmailVerification, UserRepository
from backend.domain.services import (
    EmailVerificationMailerInterface as EmailVerificationMailer,
)
from backend.domain.services import (
    EmailVerificationStoreInterface as EmailVerificationStore,
)
from backend.domain.services import PasswordServiceInterface as PasswordService


class RequestEmailVerificationUseCase:
    """Создает pending-регистрацию и отправляет код подтверждения email."""

    def __init__(
        self,
        user_repo: UserRepository,
        password_service: PasswordService,
        verification_store: EmailVerificationStore,
        mailer: EmailVerificationMailer,
    ):
        self.user_repo = user_repo
        self.password_service = password_service
        self.verification_store = verification_store
        self.mailer = mailer

    async def execute(
        self,
        email: str,
        password: str,
        username: str,
        theme: str = "neon",
    ) -> AuthResult:
        """Start registration by requesting an email verification code.

        Args:
            email: Normalized user email.
            password: Plain password.
            username: Desired username.
            theme: Preferred visual theme.

        Returns:
            AuthResult: Success with pending verification or failure redirect.
        """
        normalized_email = str(email or "").strip().lower()
        normalized_username = str(username or "").strip()
        if await self.user_repo.get_by_email(normalized_email):
            return await AuthResult.failure(
                f"Пользователь с email {normalized_email} уже существует",
                "auth.register_page",
            )

        payload = PendingEmailVerification(
            email=normalized_email,
            username=normalized_username,
            password_hash=await self.password_service.hash_password(password),
            code=await self._generate_code(),
            theme=await self._normalize_theme(theme),
        )
        await self.verification_store.save(payload)
        await self.mailer.send_verification_code(
            payload.email,
            payload.code,
            theme=payload.theme,
        )
        return await AuthResult.success(
            data=normalized_email,
            message=(
                "Мы отправили код подтверждения на почту. Введи его, чтобы завершить регистрацию."
            ),
            redirect_endpoint="auth.verify_email_page",
            redirect_email=normalized_email,
        )

    async def _generate_code(self) -> str:
        return f"{randbelow(1000000):06d}"

    async def _normalize_theme(self, value: str | None) -> str:
        normalized = str(value or "").strip().lower()
        return normalized if normalized in {"neon", "dark", "light", "rose"} else "neon"
