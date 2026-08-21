from __future__ import annotations

from backend.application.interface.services.recommendation_cache import RecommendationCacheInterface


class TestRecommendationCacheInterface:
    def test_abstract_method_names(self):
        assert {"get", "set", "invalidate"} <= set(RecommendationCacheInterface.__abstractmethods__)

    def test_cannot_be_instantiated(self):
        try:
            RecommendationCacheInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True
