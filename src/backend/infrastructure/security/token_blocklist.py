from __future__ import annotations

from hashlib import sha256

from backend.domain.services import TokenBlocklistInterface
from backend.infrastructure.cache.key_value_store import KeyValueStore


class TokenBlocklist(TokenBlocklistInterface):
    """Хранит отозванные JWT в Redis или локальном fallback-хранилище."""

    def __init__(self, store: KeyValueStore):
        self.store = store

    async def revoke(self, token: str, ttl_seconds: int):
        """Mark a token as revoked.

        Args:
            token: Token to revoke.
            ttl_seconds: TTL of the blocklist entry.
        """
        normalized_token = str(token or "").strip()
        ttl_value = max(int(ttl_seconds), 0)
        if not normalized_token or ttl_value <= 0:
            return
        await self.store.set(self._key(normalized_token), True, ttl_seconds=ttl_value)

    async def consume(self, token: str, ttl_seconds: int) -> bool:
        """Atomically revoke a token unless it was already revoked.

        Only one concurrent caller receives True, which makes refresh token
        rotation safe against double use under race conditions.

        Args:
            token: Token to consume.
            ttl_seconds: TTL of the blocklist entry.

        Returns:
            bool: True if this call revoked the token, False if it was already revoked.
        """
        normalized_token = str(token or "").strip()
        ttl_value = max(int(ttl_seconds), 0)
        if not normalized_token or ttl_value <= 0:
            return False
        return await self.store.consume(self._key(normalized_token), ttl_seconds=ttl_value)

    async def is_revoked(self, token: str) -> bool:
        """Check whether a token is currently revoked.

        Args:
            token: Token to check.

        Returns:
            bool: True if the token is revoked.
        """
        normalized_token = str(token or "").strip()
        if not normalized_token:
            return False
        return bool(await self.store.get(self._key(normalized_token), False))

    def _key(self, token: str) -> str:
        return f"jwt_blocklist:{sha256(token.encode('utf-8')).hexdigest()}"
