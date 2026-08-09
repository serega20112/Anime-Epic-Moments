from backend.application.use_cases.auth.result import AuthResult
from backend.config import Settings
from backend.domain import UserRepository
from backend.domain.services.jwt_service import JWTServiceInterface as JWTService
from backend.domain.services.password_reset_mailer import (
    PasswordResetMailerInterface as PasswordResetMailer,
)


class RequestPasswordResetUseCase:
    """Создает ссылку сброса пароля и отправляет ее на email пользователя."""

    def __init__(
            self,
            user_repo: UserRepository,
            jwt_service: JWTService,
            mailer: PasswordResetMailer,
    ):
        self.user_repo = user_repo
        self.jwt_service = jwt_service
        self.mailer = mailer

    async def execute(self, email: str, base_url: str | None = None) -> AuthResult:
        """Request a password reset link for a user.

        The response is intentionally identical whether or not the user exists
        to avoid leaking account existence. Always returns a success result.

        Args:
            email: Normalized user email.
            base_url: Base URL used to build the reset link.

        Returns:
            AuthResult: Always success toward the request page.
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            return AuthResult.success(redirect_endpoint="auth.password_reset_request_page")

        token = self.jwt_service.create_password_reset_token(
            user_id=user.id, expires_minutes=Settings.password_reset_expire_minutes
        )
        normalized_base_url = (base_url or Settings.app_base_url).rstrip("/")
        reset_link = f"{normalized_base_url}/auth/password-reset/confirm?token={token}"
        await self.mailer.send_reset_email(user.email, reset_link)
        return AuthResult.success(redirect_endpoint="auth.password_reset_request_page")
