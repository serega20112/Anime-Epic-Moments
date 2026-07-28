"""
Account lock service using Redis-backed KeyValueStore.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from src.backend.infrastructure.cache.key_value_store import KeyValueStore
from src.backend.infrastructure.security.rate_limiter import RateLimiter

logger = logging.getLogger("anime_epic_moments")

LOCK_PREFIX = "lock:user:"
ATTEMPT_SCOPE = "login_failures"
ATTEMPT_LIMIT = 5
ATTEMPT_WINDOW_SECONDS = 900  # 15 min
LOCK_DURATION_SECONDS = 1800  # 30 min


@dataclass
class AccountStatus:
    is_locked: bool
    unlock_at: str | None
    failed_attempts: int
    remaining_attempts: int
    max_attempts: int = ATTEMPT_LIMIT


class AccountLockService:
    """
    Account lockout based on KeyValueStore (Redis) with in-memory fallback.
    Uses RateLimiter for failed-attempt counting and a dedicated lock key.
    """

    def __init__(self, store: KeyValueStore):
        self.store = store
        self._rate_limiter = RateLimiter(store=store)

    async def record_failed_attempt(self, email: str) -> AccountStatus:
        normalized_email = email.strip().lower()
        decision = await self._rate_limiter.hit(
            scope=ATTEMPT_SCOPE,
            subject=normalized_email,
            limit=ATTEMPT_LIMIT,
            window_seconds=ATTEMPT_WINDOW_SECONDS,
        )

        if not decision.allowed:
            await self._lock_account(normalized_email)
            return AccountStatus(
                is_locked=True,
                unlock_at=datetime.now(timezone.utc).isoformat(),
                failed_attempts=decision.current_count,
                remaining_attempts=0,
            )

        return AccountStatus(
            is_locked=False,
            unlock_at=None,
            failed_attempts=decision.current_count,
            remaining_attempts=decision.remaining,
        )

    async def is_account_locked(self, email: str) -> tuple[bool, str | None]:
        normalized_email = email.strip().lower()
        lock_key = f"{LOCK_PREFIX}{normalized_email}"
        lock_data = await self.store.get(lock_key)
        if lock_data is None:
            return False, None

        if isinstance(lock_data, dict):
            unlock_at = lock_data.get("unlock_at")
            return True, unlock_at
        return True, str(lock_data)

    async def unlock_account(self, email: str) -> bool:
        normalized_email = email.strip().lower()
        lock_key = f"{LOCK_PREFIX}{normalized_email}"
        await self.store.delete(lock_key)
        logger.info("account_unlocked email=%s", normalized_email)
        return True

    async def get_account_status(self, email: str) -> AccountStatus:
        normalized_email = email.strip().lower()
        is_locked, unlock_at = await self.is_account_locked(normalized_email)

        # Get current attempt count from rate limiter
        attempt_key = f"rate_limit:{ATTEMPT_SCOPE}:{normalized_email}"
        attempts = await self.store.get(attempt_key) or 0

        return AccountStatus(
            is_locked=is_locked,
            unlock_at=unlock_at,
            failed_attempts=int(attempts),
            remaining_attempts=max(0, ATTEMPT_LIMIT - int(attempts)) if not is_locked else 0,
        )

    async def _lock_account(self, email: str):
        normalized_email = email.strip().lower()
        lock_key = f"{LOCK_PREFIX}{normalized_email}"
        unlock_at = datetime.now(timezone.utc).isoformat()
        await self.store.set(
            lock_key,
            {"unlock_at": unlock_at, "reason": "too_many_failed_attempts"},
            ttl_seconds=LOCK_DURATION_SECONDS,
        )
        logger.warning(
            "account_locked email=%s duration=%ds",
            normalized_email,
            LOCK_DURATION_SECONDS,
        )