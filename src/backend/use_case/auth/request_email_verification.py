from secrets import randbelow

from src.backend.domain.user.value_object import PendingEmailVerification
from src.backend.infrastructure.external.email_verification_mailer import (
    EmailVerificationMailer,
)
from src.backend.infrastructure.security.email_verification_store import (
    EmailVerificationStore,
)
from src.backend.infrastructure.security.password_service import PasswordService
from src.backend.repository.user_repository import UserRepository
from src.backend.use_case.auth.register_user import EmailAlreadyExistsError


class RequestEmailVerificationUseCase:
    """Создает pending-регистрацию и отправляет код подтверждения email."""

    def __init__(
        self,
        user_repo: UserRepository,
        password_service: PasswordService,
        verification_store: EmailVerificationStore,
        mailer: EmailVerificationMailer,
    ):
        self.user_repo = user_repo
        self.password_service = password_service
        self.verification_store = verification_store
        self.mailer = mailer

    def execute(
        self,
        email: str,
        password: str,
        username: str,
        theme: str = "neon",
    ) -> PendingEmailVerification:
        normalized_email = str(email or "").strip().lower()
        normalized_username = str(username or "").strip()
        if self.user_repo.get_by_email(normalized_email):
            raise EmailAlreadyExistsError(
                f"Пользователь с email {normalized_email} уже существует"
            )

        payload = PendingEmailVerification(
            email=normalized_email,
            username=normalized_username,
            password_hash=self.password_service.hash_password(password),
            code=self._generate_code(),
            theme=self._normalize_theme(theme),
        )
        self.verification_store.save(payload)
        self.mailer.send_verification_code(
            payload.email,
            payload.code,
            theme=payload.theme,
        )
        return payload

    def _generate_code(self) -> str:
        return f"{randbelow(1000000):06d}"

    def _normalize_theme(self, value: str | None) -> str:
        normalized = str(value or "").strip().lower()
        return normalized if normalized in {"neon", "dark", "light", "rose"} else "neon"
