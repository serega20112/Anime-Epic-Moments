"""Account lockout service using Redis-backed KeyValueStore."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from backend.infrastructure.security.rate_limiter import RateLimiter

from backend.infrastructure.cache.key_value_store import KeyValueStore

logger = logging.getLogger("anime_epic_moments")

LOCK_PREFIX = "lock:user:"
ATTEMPT_SCOPE = "login_failures"
ATTEMPT_LIMIT = 5
ATTEMPT_WINDOW_SECONDS = 900
LOCK_DURATION_SECONDS = 1800


@dataclass
class AccountStatus:
    """Represents the current lock status of a user account."""

    is_locked: bool
    unlock_at: str | None
    failed_attempts: int
    remaining_attempts: int
    max_attempts: int = ATTEMPT_LIMIT


class AccountLockService:
    """Account lockout using KeyValueStore (Redis) with in-memory fallback.

    Uses RateLimiter for failed-attempt counting and a dedicated lock key
    in KeyValueStore for temporary account blocking.
    """

    def __init__(self, store: KeyValueStore) -> None:
        self.store = store
        self._rate_limiter = RateLimiter(store=store)

    async def record_failed_attempt(self, email: str) -> AccountStatus:
        """Record a failed login attempt and lock account if limit exceeded.

        Args:
            email: User email address.

        Returns:
            AccountStatus: Current account status after recording the attempt.
        """
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
                unlock_at=(datetime.now(UTC) + timedelta(seconds=LOCK_DURATION_SECONDS)).isoformat(),
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
        """Check if an account is currently locked.

        Args:
            email: User email address.

        Returns:
            tuple[bool, str | None]: (is_locked, unlock_time_iso or None).
        """
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
        """Manually unlock an account.

        Args:
            email: User email address.

        Returns:
            bool: True after successful unlock.
        """
        normalized_email = email.strip().lower()
        lock_key = f"{LOCK_PREFIX}{normalized_email}"
        await self.store.delete(lock_key)
        logger.info("account_unlocked email=%s", normalized_email)
        return True

    async def get_account_status(self, email: str) -> AccountStatus:
        """Get detailed account lock status including attempt count.

        Args:
            email: User email address.

        Returns:
            AccountStatus: Current account status.
        """
        normalized_email = email.strip().lower()
        is_locked, unlock_at = await self.is_account_locked(normalized_email)

        attempt_key = f"rate_limit:{ATTEMPT_SCOPE}:{normalized_email}"
        attempts = await self.store.get(attempt_key) or 0

        return AccountStatus(
            is_locked=is_locked,
            unlock_at=unlock_at,
            failed_attempts=int(attempts),
            remaining_attempts=max(0, ATTEMPT_LIMIT - int(attempts)) if not is_locked else 0,
        )

    async def _lock_account(self, email: str) -> None:
        """Lock an account by setting a lock key with TTL.

        Args:
            email: Normalized user email address.
        """
        normalized_email = email.strip().lower()
        lock_key = f"{LOCK_PREFIX}{normalized_email}"
        unlock_at = (datetime.now(UTC) + timedelta(seconds=LOCK_DURATION_SECONDS)).isoformat()
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
