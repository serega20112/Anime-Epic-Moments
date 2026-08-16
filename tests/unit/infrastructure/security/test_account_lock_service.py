from __future__ import annotations

import pytest

from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.security.account_lock_service import (
    ATTEMPT_LIMIT,
    AccountLockService,
    AccountStatus,
)


@pytest.fixture
def store():
    return KeyValueStore(redis_url=None, namespace="test")


@pytest.fixture
def service(store):
    return AccountLockService(store=store)


async def test_initial_statuses_allow_login(service):
    is_locked, unlock_at = await service.is_account_locked("USER@example.com")
    assert is_locked is False
    assert unlock_at is None

    status = await service.get_account_status("user@example.com")
    assert isinstance(status, AccountStatus)
    assert status.is_locked is False


async def test_failed_attempts_accumulate(service):
    for _ in range(ATTEMPT_LIMIT - 1):
        status = await service.record_failed_attempt("user@example.com")
    assert status.is_locked is False
    assert status.failed_attempts == ATTEMPT_LIMIT - 1


async def test_account_locks_after_limit(service):
    status = None
    for _ in range(ATTEMPT_LIMIT + 1):
        status = await service.record_failed_attempt("user@example.com")

    assert status.is_locked is True
    assert status.remaining_attempts == 0
    assert status.unlock_at is not None
    assert status.failed_attempts >= ATTEMPT_LIMIT


async def test_is_account_locked_returns_lock(service):
    for _ in range(ATTEMPT_LIMIT + 1):
        await service.record_failed_attempt("user@example.com")

    is_locked, unlock_at = await service.is_account_locked("user@example.com")
    assert is_locked is True
    assert unlock_at is not None


async def test_unlock_account_clears_lock(service):
    for _ in range(ATTEMPT_LIMIT + 1):
        await service.record_failed_attempt("user@example.com")

    assert await service.unlock_account("USER@example.com") is True
    is_locked, _ = await service.is_account_locked("user@example.com")
    assert is_locked is False


async def test_get_account_status_while_locked(service):
    for _ in range(ATTEMPT_LIMIT + 1):
        await service.record_failed_attempt("user@example.com")

    status = await service.get_account_status("user@example.com")
    assert status.is_locked is True
    assert status.remaining_attempts == 0
