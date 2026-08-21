import jwt

from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.services import PasswordServiceInterface as PasswordService
from backend.application.interface.services.jwt_service import JWTServiceInterface as JWTService
from backend.application.interface.services.token_blocklist import TokenBlocklistInterface
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.application.use_cases.auth.result import AuthResult


class InvalidPasswordResetTokenError(Exception):
    """Raised when a password reset token is invalid or stale."""


class ResetPasswordUseCase:
    """Сбрасывает пароль пользователя по валидному токену."""

    def __init__(
        self,
        user_repo: UserRepository,
        jwt_service: JWTService,
        password_service: PasswordService,
        token_blocklist: TokenBlocklistInterface,
        unit_of_work: UnitOfWorkInterface,
    ):
        """Initialize the use case.

        Args:
            user_repo: User repository port.
            jwt_service: JWT service.
            password_service: Password hashing service.
            token_blocklist: Token blocklist.
            unit_of_work: Transaction boundary.
        """
        self.user_repo = user_repo
        self.jwt_service = jwt_service
        self.password_service = password_service
        self.token_blocklist = token_blocklist
        self.unit_of_work = unit_of_work

    async def execute(self, token: str, new_password: str) -> AuthResult:
        """Reset the user password within a transaction."""
        async with self.unit_of_work:
            return await self._execute(token, new_password)

    async def _execute(self, token: str, new_password: str) -> AuthResult:
        """Сбросение пароля по токену.

        Args:
            token: Password reset token.
            new_password: New plain password.

        Returns:
            AuthResult: Success toward login or failure back to confirm page.
        """
        normalized_token = str(token or "").strip()
        if not normalized_token:
            return await AuthResult.failure(
                "Ссылка для сброса пароля недействительна или устарела",
                "auth.password_reset_confirm_page",
            )
        try:
            user_id = await self.jwt_service.decode_password_reset_token(normalized_token)
        except jwt.PyJWTError:
            return await AuthResult.failure(
                "Ссылка для сброса пароля недействительна или устарела",
                "auth.password_reset_confirm_page",
            )

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return await AuthResult.failure(
                "Пользователь не найден",
                "auth.password_reset_confirm_page",
            )

        ttl_seconds = await self.jwt_service.get_token_ttl_seconds(
            normalized_token, expected_type="password_reset"
        )
        if not await self.token_blocklist.consume(normalized_token, ttl_seconds):
            return await AuthResult.failure(
                "Ссылка для сброса пароля уже использована",
                "auth.password_reset_confirm_page",
            )

        password_hash = await self.password_service.hash_password(new_password)
        await self.user_repo.update_password(user_id=user_id, password_hash=password_hash)
        return await AuthResult.success(
            message="Пароль обновлен. Теперь можно войти.",
            redirect_endpoint="auth.login_page",
        )
