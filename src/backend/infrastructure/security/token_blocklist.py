"""Список отозванных JWT-токенов."""

from __future__ import annotations

from hashlib import sha256

from backend.application.interface.services import TokenBlocklistInterface
from backend.infrastructure.cache.key_value_store import KeyValueStore


class TokenBlocklist(TokenBlocklistInterface):
    """Хранит отозванные JWT в Redis или локальном fallback-хранилище."""

    def __init__(self, store: KeyValueStore):
        """Создать список отозванных токенов поверх хранилища ключей и значений."""
        self.store = store

    async def revoke(self, token: str, ttl_seconds: int):
        """Пометить токен отозванным."""
        normalized_token = str(token or "").strip()
        ttl_value = max(int(ttl_seconds), 0)
        if not normalized_token or ttl_value <= 0:
            return
        await self.store.set(await self._key(normalized_token), True, ttl_seconds=ttl_value)

    async def consume(self, token: str, ttl_seconds: int) -> bool:
        """Атомарно отозвать токен, если он ещё не отозван.

        При одновременных запросах True получает только один, поэтому ротация
        refresh-токенов безопасна при двойных запросах.
        """
        normalized_token = str(token or "").strip()
        ttl_value = max(int(ttl_seconds), 0)
        if not normalized_token or ttl_value <= 0:
            return False
        return await self.store.consume(await self._key(normalized_token), ttl_seconds=ttl_value)

    async def is_revoked(self, token: str) -> bool:
        """Проверить, отозван ли токен сейчас."""
        normalized_token = str(token or "").strip()
        if not normalized_token:
            return False
        return bool(await self.store.get(await self._key(normalized_token), False))

    async def _key(self, token: str) -> str:
        return f"jwt_blocklist:{sha256(token.encode('utf-8')).hexdigest()}"
