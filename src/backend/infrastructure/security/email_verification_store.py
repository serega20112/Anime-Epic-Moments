from src.backend.domain.user.value_object import PendingEmailVerification
from src.backend.infrastructure.cache.key_value_store import KeyValueStore


class EmailVerificationStore:
    """Хранит ожидающие подтверждения email регистрации с TTL."""

    def __init__(
        self,
        store: KeyValueStore,
        ttl_seconds: int = 600,
    ):
        self.store = store
        self.ttl_seconds = max(int(ttl_seconds), 60)
        self.prefix = "email_verification"

    def save(self, payload: PendingEmailVerification) -> PendingEmailVerification:
        self.store.set(
            self._key(payload.email),
            payload,
            ttl_seconds=self.ttl_seconds,
        )
        return payload

    def get(self, email: str) -> PendingEmailVerification | None:
        value = self.store.get(self._key(email))
        return value if isinstance(value, PendingEmailVerification) else None

    def delete(self, email: str):
        self.store.delete(self._key(email))

    def get_ttl_seconds(self, email: str) -> int:
        return self.store.get_ttl(self._key(email))

    def _key(self, email: str) -> str:
        return f"{self.prefix}:{str(email or '').strip().lower()}"
