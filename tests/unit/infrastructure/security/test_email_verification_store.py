from __future__ import annotations

import pytest

from backend.domain import PendingEmailVerification
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.security.email_verification_store import (
    EmailVerificationStore,
)


@pytest.mark.unit
async def test_email_verification_store_saves_gets_and_deletes_pending_registration():
    """Проверяем, что EmailVerificationStore сохраняет pending-регистрацию, читает ее и удаляет по email."""
    store = EmailVerificationStore(KeyValueStore(redis_url=None, namespace="test"), ttl_seconds=120)
    payload = PendingEmailVerification(
        email="user@example.com",
        username="tester",
        password_hash="hashed-password",
        code="123456",
        theme="dark",
    )

    await store.save(payload)

    assert await store.get("User@Example.com") == payload
    ttl_seconds = await store.get_ttl_seconds("user@example.com")
    assert 0 < ttl_seconds <= 120

    await store.delete("user@example.com")

    assert await store.get("user@example.com") is None
    assert await store.get_ttl_seconds("user@example.com") == 0