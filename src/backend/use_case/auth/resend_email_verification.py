from secrets import randbelow

from src.backend.domain.user.value_object import PendingEmailVerification
from src.backend.infrastructure.external.email_verification_mailer import (
    EmailVerificationMailer,
)
from src.backend.infrastructure.security.email_verification_store import (
    EmailVerificationStore,
)


class PendingEmailVerificationNotFoundError(Exception):
    pass


class ResendEmailVerificationUseCase:
    """Перевыпускает код подтверждения для ожидающей регистрации."""

    def __init__(
        self,
        verification_store: EmailVerificationStore,
        mailer: EmailVerificationMailer,
    ):
        self.verification_store = verification_store
        self.mailer = mailer

    async def execute(self, email: str) -> PendingEmailVerification:
        normalized_email = str(email or "").strip().lower()
        payload = await self.verification_store.get(normalized_email)
        if payload is None:
            raise PendingEmailVerificationNotFoundError(
                "Не найдена ожидающая регистрация для этого email."
            )
        refreshed = PendingEmailVerification(
            email=payload.email,
            username=payload.username,
            password_hash=payload.password_hash,
            code=self._generate_code(),
            theme=payload.theme,
        )
        await self.verification_store.save(refreshed)
        await self.mailer.send_verification_code(
            refreshed.email,
            refreshed.code,
            theme=refreshed.theme,
        )
        return refreshed

    def _generate_code(self) -> str:
        return f"{randbelow(1000000):06d}"
