from __future__ import annotations

import pytest

from backend.infrastructure.external._async import external_method


class _Blocking:
    def __init__(self):
        self.calls = []

    @external_method
    def work(self, value: int) -> int:
        self.calls.append(value)
        return value * 2


async def test_external_method_makes_sync_callable_awaitable():
    blocking = _Blocking()
    result = await blocking.work(21)
    assert result == 42
    assert blocking.calls == [21]


async def test_external_method_runs_in_worker_thread():
    import threading

    blocking = _Blocking()

    def run():
        import asyncio

        return asyncio.run(blocking.work(1))

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run)
        assert future.result() == 2