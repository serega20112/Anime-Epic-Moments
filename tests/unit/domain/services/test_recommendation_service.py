from __future__ import annotations

from backend.domain.services.recommendation_service import RecommendationServiceInterface


class TestRecommendationServiceInterface:
    def test_abstract_method_names(self):
        assert {"generate_recommendations", "refresh_recommendations"} <= set(
            RecommendationServiceInterface.__abstractmethods__
        )

    def test_cannot_be_instantiated(self):
        try:
            RecommendationServiceInterface()  # type: ignore[abstract]
            raised = False
        except TypeError:
            raised = True
        assert raised is True
