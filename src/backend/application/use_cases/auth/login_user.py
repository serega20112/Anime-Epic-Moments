"""Use case for authenticating a user with email and password."""

from __future__ import annotations

from backend.application.use_cases.auth.result import AuthResult
from backend.domain import UserRepository
from backend.domain.services import PasswordServiceInterface as PasswordService

_ACCOUNT_LOCKED_MESSAGE = (
    "Аккаунт временно заблокирован из-за множества неудачных "
    "попыток входа. Попробуйте позже."
)
_INVALID_CREDENTIALS_MESSAGE = "Неверный email или пароль"


def _welcome_message(username: str) -> str:
    """Build the login success flash message.

    Args:
        username: Authenticated username.

    Returns:
        str: Welcome message.
    """
    return f"Добро пожаловать, {username}!"


class LoginUserUseCase:
    """Verify credentials and return the authenticated user aggregate.

    Enforces account lockout: fully locked accounts are rejected before any
    credential check, failed attempts are recorded, and a successful login
    resets the attempt counter.
    """

    def __init__(
            self,
            user_repository: UserRepository,
            password_service: PasswordService,
            account_lock_service=None,
    ):
        """Initialize the use case.

        Args:
            user_repository: User repository port.
            password_service: Password hashing/verification service.
            account_lock_service: Optional account lockout service.
        """
        self.user_repository = user_repository
        self.password_service = password_service
        self.account_lock_service = account_lock_service

    async def execute(self, *, email: str, password: str) -> AuthResult:
        """Authenticate a user by email and password.

        Args:
            email: Normalized user email.
            password: Plain password.

        Returns:
            AuthResult: Success with the user or failure with redirect info.
        """
        locked = await self._ensure_not_locked(email)
        if locked is not None:
            return locked
        user = await self.user_repository.get_by_email(email)
        if not user or not self.password_service.verify_password(password, user.password_hash):
            await self._record_failure(email)
            return AuthResult.failure(
                _INVALID_CREDENTIALS_MESSAGE,
                "auth.login_page",
            )
        await self._reset_on_success(email)
        return AuthResult.success(
            data=user,
            message=_welcome_message(user.username),
            redirect_endpoint="index.index",
        )

    async def _ensure_not_locked(self, email: str) -> AuthResult | None:
        """Return a failure result when an account is locked.

        Args:
            email: Normalized user email.

        Returns:
            AuthResult | None: Failure when locked, else None.
        """
        if self.account_lock_service is None:
            return None
        is_locked, _unlock_at = await self.account_lock_service.is_account_locked(email)
        if is_locked:
            return AuthResult.failure(_ACCOUNT_LOCKED_MESSAGE, "auth.login_page")
        return None

    async def _record_failure(self, email: str) -> None:
        """Record a failed login attempt.

        Args:
            email: Normalized user email.
        """
        if self.account_lock_service is not None:
            await self.account_lock_service.record_failed_attempt(email)

    async def _reset_on_success(self, email: str) -> None:
        """Reset the lock state after a successful login.

        Args:
            email: Normalized user email.
        """
        if self.account_lock_service is not None:
            await self.account_lock_service.unlock_account(email)
