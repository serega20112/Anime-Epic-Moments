"""
Use case для логина пользователя.
Проверяет email и пароль, возвращает агрегат User.
"""

from src.backend.domain.user.entity import User
from src.backend.infrastructure.security.password_service import PasswordService
from src.backend.repository.user_repository import UserRepository


class InvalidCredentialsError(Exception):
    pass


class LoginUserUseCase:
    def __init__(self, user_repo: UserRepository, password_service: PasswordService):
        self.user_repo = user_repo
        self.password_service = password_service

    def execute(self, email: str, password: str) -> User:
        user = self.user_repo.get_by_email(email)
        if not user or not self.password_service.verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Неверный email или пароль")
        return user
