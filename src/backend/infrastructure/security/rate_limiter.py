from __future__ import annotations

from dataclasses import dataclass

from src.backend.infrastructure.cache.key_value_store import KeyValueStore


@dataclass
class RateLimitDecision:
    allowed: bool
    current_count: int
    remaining: int
    retry_after: int


class RateLimiter:
    """Ограничивает частоту действий по субъекту и окну времени."""

    def __init__(self, store: KeyValueStore):
        self.store = store

    async def hit(
        self,
        scope: str,
        subject: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        normalized_scope = str(scope or "default").strip().lower()
        normalized_subject = str(subject or "anonymous").strip().lower()
        key = f"rate_limit:{normalized_scope}:{normalized_subject}"
        current_count = await self.store.increment(
            key,
            ttl_seconds=max(int(window_seconds), 1),
            amount=1,
        )
        retry_after = await self.store.get_ttl(key)
        allowed = current_count <= int(limit)
        return RateLimitDecision(
            allowed=allowed,
            current_count=current_count,
            remaining=max(int(limit) - current_count, 0),
            retry_after=max(int(retry_after), 0),
        )
