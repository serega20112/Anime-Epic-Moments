from __future__ import annotations

import pytest

from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.security.token_blocklist import TokenBlocklist


@pytest.mark.unit
async def test_token_blocklist_marks_token_as_revoked():
    """Проверяем, что TokenBlocklist помечает токен как отозванный на заданный TTL."""
    blocklist = TokenBlocklist(KeyValueStore(redis_url=None, namespace="test"))

    await blocklist.revoke("token-value", ttl_seconds=60)

    assert await blocklist.is_revoked("token-value") is True


@pytest.mark.unit
async def test_token_blocklist_ignores_empty_or_expired_revoke_requests():
    """Проверяем, что TokenBlocklist не сохраняет пустые токены и TTL <= 0."""
    blocklist = TokenBlocklist(KeyValueStore(redis_url=None, namespace="test"))
    await blocklist.revoke("", ttl_seconds=60)
    await blocklist.revoke("token-value", ttl_seconds=0)

    assert await blocklist.is_revoked("") is False
    assert await blocklist.is_revoked("token-value") is False


@pytest.mark.unit
async def test_token_blocklist_consumes_token_exactly_once():
    """Проверяем, что TokenBlocklist.consume атомарно отзывает токен один раз."""
    blocklist = TokenBlocklist(KeyValueStore(redis_url=None, namespace="test"))

    assert await blocklist.consume("single-use-token", ttl_seconds=60) is True
    assert await blocklist.consume("single-use-token", ttl_seconds=60) is False
    assert await blocklist.is_revoked("single-use-token") is True


@pytest.mark.unit
async def test_token_blocklist_consume_ignores_blank_token():
    """Проверяем, что TokenBlocklist.consume не отзывает пустой токен."""
    blocklist = TokenBlocklist(KeyValueStore(redis_url=None, namespace="test"))

    assert await blocklist.consume("", ttl_seconds=60) is False
    assert await blocklist.consume("token", ttl_seconds=0) is False
