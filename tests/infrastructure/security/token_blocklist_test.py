from __future__ import annotations

from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.security.token_blocklist import TokenBlocklist


def test_token_blocklist_marks_token_as_revoked():
    """Проверяем, что TokenBlocklist помечает токен как отозванный на заданный TTL."""
    blocklist = TokenBlocklist(KeyValueStore(redis_url=None, namespace="test"))

    blocklist.revoke("token-value", ttl_seconds=60)

    assert blocklist.is_revoked("token-value") is True


def test_token_blocklist_ignores_empty_or_expired_revoke_requests():
    """Проверяем, что TokenBlocklist не сохраняет пустые токены и TTL <= 0."""
    blocklist = TokenBlocklist(KeyValueStore(redis_url=None, namespace="test"))
    blocklist.revoke("", ttl_seconds=60)
    blocklist.revoke("token-value", ttl_seconds=0)

    assert blocklist.is_revoked("") is False
    assert blocklist.is_revoked("token-value") is False
