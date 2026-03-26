"""
Use case для регистрации нового пользователя.
Проверяет уникальность email и создает агрегат User.
"""

from src.backend.domain.user.entity import User
from src.backend.infrastructure.security.password_service import PasswordService
from src.backend.repository.user_repository import UserRepository


class EmailAlreadyExistsError(Exception):
    pass


class RegisterUserUseCase:
    def __init__(self, user_repo: UserRepository, password_service: PasswordService):
        self.user_repo = user_repo
        self.password_service = password_service

    def execute(self, email: str, password: str, username: str):
        if self.user_repo.get_by_email(email):
            raise EmailAlreadyExistsError(
                f"Пользователь с email {email} уже существует"
            )

        password_hash = self.password_service.hash_password(password)
        user = User(email=email, username=username, password_hash=password_hash)
        return self.user_repo.add(user)
