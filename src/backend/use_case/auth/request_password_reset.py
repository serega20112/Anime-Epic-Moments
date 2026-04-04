from src.backend.dependencies.settings import Settings
from src.backend.infrastructure.external.password_reset_mailer import (
    PasswordResetMailer,
)
from src.backend.infrastructure.security.jwt_service import JWTService
from src.backend.repository.user_repository import UserRepository


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

    async def execute(self, email: str, base_url: str | None = None) -> None:
        """Принимает email пользователя и отправляет письмо, если пользователь найден."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            return

        token = self.jwt_service.create_password_reset_token(
            user_id=user.id, expires_minutes=Settings.password_reset_expire_minutes
        )
        normalized_base_url = (base_url or Settings.app_base_url).rstrip("/")
        reset_link = f"{normalized_base_url}/auth/password-reset/confirm?token={token}"
        await self.mailer.send_reset_email(user.email, reset_link)
