"""Хранилище ожидающих подтверждений адреса почты."""

from backend.domain import PendingEmailVerification
from backend.infrastructure.cache.key_value_store import KeyValueStore


class EmailVerificationStore:
    """Хранит ожидающие подтверждения email регистрации с TTL."""

    def __init__(
        self,
        store: KeyValueStore,
        ttl_seconds: int = 600,
    ):
        """Создать хранилище подтверждений с заданным сроком жизни записей."""
        self.store = store
        self.ttl_seconds = max(int(ttl_seconds), 60)
        self.prefix = "email_verification"

    async def save(self, payload: PendingEmailVerification) -> PendingEmailVerification:
        """Сохранить ожидающее подтверждение адреса почты."""
        await self.store.set(
            await self._key(payload.email),
            payload,
            ttl_seconds=self.ttl_seconds,
        )
        return payload

    async def get(self, email: str) -> PendingEmailVerification | None:
        """Прочитать ожидающее подтверждение по адресу почты."""
        value = await self.store.get(await self._key(email))
        return value if isinstance(value, PendingEmailVerification) else None

    async def delete(self, email: str):
        """Удалить ожидающее подтверждение адреса почты."""
        await self.store.delete(await self._key(email))

    async def get_ttl_seconds(self, email: str) -> int:
        """Вернуть остаток жизни записи подтверждения в секундах."""
        return await self.store.get_ttl(await self._key(email))

    async def _key(self, email: str) -> str:
        return f"{self.prefix}:{str(email or '').strip().lower()}"
