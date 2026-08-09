import jwt

from backend.application.use_cases.auth.result import AuthResult
from backend.domain import UserRepository
from backend.domain.services import PasswordServiceInterface as PasswordService
from backend.domain.services.jwt_service import JWTServiceInterface as JWTService


class InvalidPasswordResetTokenError(Exception):
    """Raised when a password reset token is invalid or stale."""


class ResetPasswordUseCase:
    """Сбрасывает пароль пользователя по валидному токену."""

    def __init__(
            self,
            user_repo: UserRepository,
            jwt_service: JWTService,
            password_service: PasswordService,
    ):
        """Initialize the use case.

        Args:
            user_repo: User repository port.
            jwt_service: JWT service.
            password_service: Password hashing service.
        """
        self.user_repo = user_repo
        self.jwt_service = jwt_service
        self.password_service = password_service

    async def execute(self, token: str, new_password: str) -> AuthResult:
        """Сбросение пароля по токену.

        Args:
            token: Password reset token.
            new_password: New plain password.

        Returns:
            AuthResult: Success toward login or failure back to confirm page.
        """
        try:
            user_id = self.jwt_service.decode_password_reset_token(token)
        except jwt.PyJWTError:
            return AuthResult.failure(
                "Ссылка для сброса пароля недействительна или устарела",
                "auth.password_reset_confirm_page",
            )

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return AuthResult.failure(
                "Пользователь не найден",
                "auth.password_reset_confirm_page",
            )

        password_hash = self.password_service.hash_password(new_password)
        await self.user_repo.update_password(user_id=user_id, password_hash=password_hash)
        return AuthResult.success(
            message="Пароль обновлен. Теперь можно войти.",
            redirect_endpoint="auth.login_page",
        )
