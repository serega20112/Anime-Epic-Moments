"""Facade re-exports for backend.infrastructure.cache."""

from __future__ import annotations

from backend.infrastructure.cache.highlight_dashboard_cache import HighlightDashboardCache
from backend.infrastructure.cache.recommendation_cache import RecommendationCache

__all__ = [
    "HighlightDashboardCache",
    "RecommendationCache",
]
