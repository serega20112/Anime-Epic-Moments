from __future__ import annotations

from backend.application.use_cases.watch.result import WatchResult


class TestWatchResult:
    async def test_success(self):
        result = await WatchResult.success(data="w")
        assert result.ok is True
        assert result.data == "w"
        assert result.status_code == 200

    async def test_failure(self):
        result = await WatchResult.failure("bad", status_code=400)
        assert result.ok is False
        assert result.error == "bad"
        assert result.status_code == 400
