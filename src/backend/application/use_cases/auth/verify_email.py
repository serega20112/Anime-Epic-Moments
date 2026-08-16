from backend.application.use_cases.auth.result import AuthResult
from backend.domain import User, UserRepository
from backend.domain.services import (
    EmailVerificationStoreInterface as EmailVerificationStore,
)
from backend.domain.unit_of_work import UnitOfWorkInterface


class EmailVerificationExpiredError(Exception):
    """Raised when a verification payload has expired or is missing."""


class InvalidEmailVerificationCodeError(Exception):
    """Raised when the supplied verification code does not match."""


class VerifyEmailUseCase:
    """Подтверждает email кодом и создает пользователя после успешной проверки."""

    def __init__(
        self,
        user_repo: UserRepository,
        verification_store: EmailVerificationStore,
        unit_of_work: UnitOfWorkInterface,
    ):
        """Initialize the use case.

        Args:
            user_repo: User repository port.
            verification_store: Verification code store.
            unit_of_work: Transaction boundary.
        """
        self.user_repo = user_repo
        self.verification_store = verification_store
        self.unit_of_work = unit_of_work

    async def execute(self, email: str, code: str) -> AuthResult:
        """Verify an email code and create a user within a transaction."""
        async with self.unit_of_work:
            return await self._execute(email, code)

    async def _execute(self, email: str, code: str) -> AuthResult:
        """Confirm an email code and create a user.

        Args:
            email: Normalized user email.
            code: Verification code.

        Returns:
            AuthResult: Success with the created user or failure redirect.
        """
        normalized_email = str(email or "").strip().lower()
        normalized_code = str(code or "").strip()
        payload = await self.verification_store.get(normalized_email)
        if payload is None:
            return AuthResult.failure(
                "Код подтверждения истёк. Запроси новый.",
                "auth.verify_email_page",
                redirect_email=normalized_email,
            )
        if payload.code != normalized_code:
            return AuthResult.failure(
                "Неверный код подтверждения.",
                "auth.verify_email_page",
                redirect_email=normalized_email,
            )
        if await self.user_repo.get_by_email(normalized_email):
            await self.verification_store.delete(normalized_email)
            return AuthResult.failure(
                f"Пользователь с email {normalized_email} уже существует",
                "auth.verify_email_page",
                redirect_email=normalized_email,
            )

        user = User(
            email=payload.email,
            username=payload.username,
            password_hash=payload.password_hash,
        )
        created_user = await self.user_repo.add(user)
        await self.verification_store.delete(normalized_email)
        return AuthResult.success(
            data=created_user,
            message=f"Добро пожаловать, {created_user.username}!",
            redirect_endpoint="index.index",
        )
