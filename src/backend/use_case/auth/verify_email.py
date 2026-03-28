from src.backend.domain.user.entity import User
from src.backend.infrastructure.security.email_verification_store import (
    EmailVerificationStore,
)
from src.backend.repository.user_repository import UserRepository
from src.backend.use_case.auth.register_user import EmailAlreadyExistsError


class EmailVerificationExpiredError(Exception):
    pass


class InvalidEmailVerificationCodeError(Exception):
    pass


class VerifyEmailUseCase:
    """Подтверждает email кодом и создает пользователя после успешной проверки."""

    def __init__(
        self,
        user_repo: UserRepository,
        verification_store: EmailVerificationStore,
    ):
        self.user_repo = user_repo
        self.verification_store = verification_store

    def execute(self, email: str, code: str) -> User:
        normalized_email = str(email or "").strip().lower()
        normalized_code = str(code or "").strip()
        payload = self.verification_store.get(normalized_email)
        if payload is None:
            raise EmailVerificationExpiredError("Код подтверждения истёк. Запроси новый.")
        if payload.code != normalized_code:
            raise InvalidEmailVerificationCodeError("Неверный код подтверждения.")
        if self.user_repo.get_by_email(normalized_email):
            self.verification_store.delete(normalized_email)
            raise EmailAlreadyExistsError(
                f"Пользователь с email {normalized_email} уже существует"
            )

        user = User(
            email=payload.email,
            username=payload.username,
            password_hash=payload.password_hash,
        )
        created_user = self.user_repo.add(user)
        self.verification_store.delete(normalized_email)
        return created_user
