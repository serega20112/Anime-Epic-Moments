"""Use case for registering a new user aggregate."""

from __future__ import annotations

from backend.domain import User
from backend.domain import UserRepository
from backend.domain.services import PasswordServiceInterface as PasswordService


class EmailAlreadyExistsError(Exception):
    """Raised when the email is already registered."""


class RegisterUserUseCase:
    """Create a new user when the email is not yet registered."""

    def __init__(self, user_repository: UserRepository, password_service: PasswordService):
        """Initialize the use case.

        Args:
            user_repository: User repository port.
            password_service: Password hashing service.
        """
        self.user_repository = user_repository
        self.password_service = password_service

    async def execute(
            self, *, email: str, password: str, username: str, theme: str = "neon"
    ) -> User:
        """Register a user and return the persisted aggregate.

        Args:
            email: Normalized user email.
            password: Plain password to hash.
            username: Desired username.
            theme: UI theme preference.

        Returns:
            User: Persisted user aggregate.

        Raises:
            EmailAlreadyExistsError: If the email is already registered.
        """
        if await self.user_repository.get_by_email(email):
            raise EmailAlreadyExistsError(f"Пользователь с email {email} уже существует")
        password_hash = self.password_service.hash_password(password)
        user = User(email=email, username=username, password_hash=password_hash)
        return await self.user_repository.add(user)
