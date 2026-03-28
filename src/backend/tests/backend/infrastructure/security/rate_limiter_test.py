from __future__ import annotations

import pytest

from src.backend.infrastructure.cache.key_value_store import KeyValueStore
from src.backend.infrastructure.security.rate_limiter import RateLimiter


@pytest.mark.parametrize(
    ("attempts", "limit", "expected_allowed"),
    [
        (1, 2, True),
        (2, 2, True),
        (3, 2, False),
    ],
)
def test_rate_limiter_blocks_after_limit(attempts, limit, expected_allowed):
    """Проверяем, что RateLimiter начинает блокировать запросы после превышения лимита."""
    limiter = RateLimiter(KeyValueStore(redis_url=None, namespace="test"))
    decision = None

    for _ in range(attempts):
        decision = limiter.hit("login", "127.0.0.1", limit=limit, window_seconds=60)

    assert decision is not None
    assert decision.allowed is expected_allowed


def test_rate_limiter_tracks_retry_after():
    """Проверяем, что RateLimiter возвращает retry_after для заблокированного ключа."""
    limiter = RateLimiter(KeyValueStore(redis_url=None, namespace="test"))
    limiter.hit("search", "user", limit=1, window_seconds=60)

    decision = limiter.hit("search", "user", limit=1, window_seconds=60)

    assert decision.allowed is False
    assert decision.retry_after >= 0
