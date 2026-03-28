from __future__ import annotations

from hashlib import sha256

from src.backend.infrastructure.cache.key_value_store import KeyValueStore


class TokenBlocklist:
    """Хранит отозванные JWT в Redis или локальном fallback-хранилище."""

    def __init__(self, store: KeyValueStore):
        self.store = store

    def revoke(self, token: str, ttl_seconds: int):
        normalized_token = str(token or "").strip()
        ttl_value = max(int(ttl_seconds), 0)
        if not normalized_token or ttl_value <= 0:
            return
        self.store.set(self._key(normalized_token), True, ttl_seconds=ttl_value)

    def is_revoked(self, token: str) -> bool:
        normalized_token = str(token or "").strip()
        if not normalized_token:
            return False
        return bool(self.store.get(self._key(normalized_token), False))

    def _key(self, token: str) -> str:
        return f"jwt_blocklist:{sha256(token.encode('utf-8')).hexdigest()}"
