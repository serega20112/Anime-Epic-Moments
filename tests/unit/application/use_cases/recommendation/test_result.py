from __future__ import annotations

from backend.application.use_cases.recommendation.result import RecommendationUseCaseResult


class TestRecommendationUseCaseResult:
    async def test_success(self):
        result = await RecommendationUseCaseResult.success(data=["a"], status_code=200)
        assert result.ok is True
        assert result.data == ["a"]
        assert result.status_code == 200

    async def test_failure(self):
        result = await RecommendationUseCaseResult.failure("upstream", status_code=503)
        assert result.ok is False
        assert result.error == "upstream"
        assert result.status_code == 503
