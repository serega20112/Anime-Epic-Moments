"""Блокировка аккаунта после неудачных попыток входа."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from backend.application.interface.services import AccountLockServiceInterface
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.security.rate_limiter import RateLimiter

logger = logging.getLogger("anime_epic_moments")

LOCK_PREFIX = "lock:user:"
ATTEMPT_SCOPE = "login_failures"
ATTEMPT_LIMIT = 5
ATTEMPT_WINDOW_SECONDS = 900
LOCK_DURATION_SECONDS = 1800


@dataclass
class AccountStatus:
    """Текущее состояние блокировки аккаунта.

    Attributes:
        is_locked: Заблокирован ли аккаунт сейчас.
        unlock_at: Момент автоматической разблокировки.
        failed_attempts: Сколько неудачных попыток уже учтено.
        remaining_attempts: Сколько попыток осталось до блокировки.
        max_attempts: Предел неудачных попыток.
    """

    is_locked: bool
    unlock_at: str | None
    failed_attempts: int
    remaining_attempts: int
    max_attempts: int = ATTEMPT_LIMIT


class AccountLockService(AccountLockServiceInterface):
    """Блокировка аккаунта поверх хранилища ключей и значений.

    Неудачные попытки считает ограничитель частоты, а признак блокировки
    хранится отдельным ключом с ограниченным сроком жизни. Срок блокировки
    приходит из конфигурации; значение по умолчанию равно константе модуля.
    """

    def __init__(
        self, store: KeyValueStore, *, lock_duration_seconds: int = LOCK_DURATION_SECONDS
    ) -> None:
        """Создать сервис блокировки поверх хранилища ключей и значений.

        Args:
            store: Хранилище ключей и значений для счётчиков и метки блокировки.
            lock_duration_seconds: Срок жизни блокировки в секундах.
        """
        self.store = store
        self._lock_duration_seconds = int(lock_duration_seconds)
        self._rate_limiter = RateLimiter(store=store)

    async def record_failed_attempt(self, email: str) -> AccountStatus:
        """Учесть неудачную попытку входа и заблокировать аккаунт при перерасходе."""
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
                unlock_at=(
                    datetime.now(UTC) + timedelta(seconds=self._lock_duration_seconds)
                ).isoformat(),
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
        """Проверить, заблокирован ли аккаунт сейчас."""
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
        """Снять блокировку аккаунта вручную."""
        normalized_email = email.strip().lower()
        lock_key = f"{LOCK_PREFIX}{normalized_email}"
        await self.store.delete(lock_key)
        logger.info("account_unlocked email=%s", normalized_email)
        return True

    async def get_account_status(self, email: str) -> AccountStatus:
        """Вернуть подробное состояние блокировки с числом попыток."""
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
        """Заблокировать аккаунт, записав ключ блокировки с ограниченным сроком."""
        normalized_email = email.strip().lower()
        lock_key = f"{LOCK_PREFIX}{normalized_email}"
        unlock_at = (datetime.now(UTC) + timedelta(seconds=self._lock_duration_seconds)).isoformat()
        await self.store.set(
            lock_key,
            {"unlock_at": unlock_at, "reason": "too_many_failed_attempts"},
            ttl_seconds=self._lock_duration_seconds,
        )
        logger.warning(
            "account_locked email=%s duration=%ds",
            normalized_email,
            self._lock_duration_seconds,
        )
