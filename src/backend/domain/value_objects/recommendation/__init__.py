"""Значимые объекты рекомендаций."""

from backend.domain.value_objects.recommendation.candidate_score import CandidateScore
from backend.domain.value_objects.recommendation.recommendation_result import (
    RecommendationResult,
)

__all__ = ["CandidateScore", "RecommendationResult"]
