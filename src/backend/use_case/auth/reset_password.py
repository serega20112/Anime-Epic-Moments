import jwt
from src.backend.infrastructure.security.jwt_service import JWTService
from src.backend.infrastructure.security.password_service import PasswordService
from src.backend.repository.user_repository import UserRepository


class InvalidPasswordResetTokenError(Exception):
    pass


class ResetPasswordUseCase:
    """Проверяет reset token и сохраняет новый пароль пользователя."""

    def __init__(
        self,
        user_repo: UserRepository,
        jwt_service: JWTService,
        password_service: PasswordService
    ):
        self.user_repo = user_repo
        self.jwt_service = jwt_service
        self.password_service = password_service

    def execute(self, token: str, new_password: str):
        """Принимает reset token и новый пароль, возвращает обновленного пользователя."""
        try:
            user_id = self.jwt_service.decode_password_reset_token(token)
        except jwt.PyJWTError as exc:
            raise InvalidPasswordResetTokenError("Ссылка для сброса пароля недействительна или устарела") from exc

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise InvalidPasswordResetTokenError("Пользователь не найден")

        password_hash = self.password_service.hash_password(new_password)
        return self.user_repo.update_password(user_id=user_id, password_hash=password_hash)
