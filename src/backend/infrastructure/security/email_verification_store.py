from backend.domain import PendingEmailVerification
from backend.infrastructure.cache.key_value_store import KeyValueStore


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

    async def save(self, payload: PendingEmailVerification) -> PendingEmailVerification:
        await self.store.set(
            self._key(payload.email),
            payload,
            ttl_seconds=self.ttl_seconds,
        )
        return payload

    async def get(self, email: str) -> PendingEmailVerification | None:
        value = await self.store.get(self._key(email))
        return value if isinstance(value, PendingEmailVerification) else None

    async def delete(self, email: str):
        await self.store.delete(self._key(email))

    async def get_ttl_seconds(self, email: str) -> int:
        return await self.store.get_ttl(self._key(email))

    def _key(self, email: str) -> str:
        return f"{self.prefix}:{str(email or '').strip().lower()}"
