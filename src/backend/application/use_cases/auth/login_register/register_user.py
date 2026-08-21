"""Use case for registering a new user aggregate."""

from __future__ import annotations

from backend.application.interface.repositories.user_repository import UserRepository
from backend.application.interface.services import PasswordServiceInterface as PasswordService
from backend.application.interface.unit_of_work import UnitOfWorkInterface
from backend.domain import User


class EmailAlreadyExistsError(Exception):
    """Raised when the email is already registered."""


class RegisterUserUseCase:
    """Create a new user when the email is not yet registered."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_service: PasswordService,
        unit_of_work: UnitOfWorkInterface,
    ):
        """Initialize the use case.

        Args:
            user_repository: User repository port.
            password_service: Password hashing service.
            unit_of_work: Transaction boundary.
        """
        self.user_repository = user_repository
        self.password_service = password_service
        self.unit_of_work = unit_of_work

    async def execute(
        self, *, email: str, password: str, username: str, theme: str = "neon"
    ) -> User:
        """Register a user within a transaction."""
        async with self.unit_of_work:
            return await self._execute(
                email=email, password=password, username=username, theme=theme
            )

    async def _execute(
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
        password_hash = await self.password_service.hash_password(password)
        user = User(email=email, username=username, password_hash=password_hash)
        return await self.user_repository.add(user)
